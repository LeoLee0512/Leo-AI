"""Full training checkpoints: everything an exact resume needs, and nothing that hides state.

The first annulus attempt saved model weights and nothing else, which is why the
retrospective budget-only continuation of its ten seeds turned out to be impossible
(``docs/pinn-trust-loop/ANNULUS_BUDGET_DIAGNOSIS_REPORT_20260918.md``). Weights alone
are not the optimizer: Adam carries its own first and second moment estimates and its
own step counter, the LR schedule carries a position, and the batch order carries a
generator state and a cursor. Reloading weights into a fresh Adam is a *different*
optimization trajectory, not a continuation of the old one, and calling it one would
be a false claim about what was measured.

So a checkpoint here is the whole resumable state:

    modelState              the parameters
    optimizerState          Adam m_t, v_t and its step counter, plus the param groups
    scheduler               gamma, last_epoch and the prefix horizon they belong to
    currentStep             how many optimization steps have been taken
    batchGeneratorState     the torch.Generator that draws the shuffles
    order / cursor          the current permutation and how far into it we are
    rngStates               the global CPU (and CUDA) RNG states
    seeds / device          identity of the trajectory this state belongs to

Everything is stored as JSON: a checkpoint is evidence, and evidence that needs a
particular library version to be read is evidence that can quietly stop being readable.
Tensors survive the round trip through ``_encode`` / ``_decode`` with their dtype.
"""

from __future__ import annotations

from typing import Any, Mapping

#: Bumped when the stored layout changes in a way a reader must notice.
CHECKPOINT_SCHEMA = "pinn.annulus.checkpoint/1.0"


def _encode(value: Any) -> Any:
    """Tensors become tagged dicts; everything else passes through unchanged."""

    import torch  # type: ignore[import-not-found]

    if isinstance(value, torch.Tensor):
        name = str(value.dtype)
        return {"__tensor__": {"dtype": name[6:] if name.startswith("torch.") else name,
                               "shape": list(value.shape),
                               "data": value.detach().cpu().flatten().tolist()}}
    if isinstance(value, Mapping):
        return {str(k): _encode(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_encode(v) for v in value]
    return value


def _decode(value: Any, *, device: str = "cpu") -> Any:
    import torch  # type: ignore[import-not-found]

    if isinstance(value, Mapping) and set(value) == {"__tensor__"}:
        spec = value["__tensor__"]
        tensor = torch.tensor(spec["data"], dtype=getattr(torch, spec["dtype"]))
        return tensor.reshape(spec["shape"]).to(device)
    if isinstance(value, Mapping):
        return {k: _decode(v, device=device) for k, v in value.items()}
    if isinstance(value, list):
        return [_decode(v, device=device) for v in value]
    return value


def _int_keys(state: Mapping[str, Any]) -> dict[Any, Any]:
    """JSON turns Adam's integer parameter indices into strings; turn them back."""

    out: dict[Any, Any] = {}
    for key, value in state.items():
        out[int(key) if isinstance(key, str) and key.lstrip("-").isdigit() else key] = value
    return out


def capture(torch, model, optimizer, scheduler, *, step: int, prefix_steps: int, order, cursor: int,
            batch_generator, device, seeds: Mapping[str, int], extra: Mapping[str, Any] | None = None
            ) -> dict[str, Any]:
    """The complete resumable state after ``step`` optimization steps."""

    rng: dict[str, Any] = {"cpu": _encode(torch.get_rng_state())}
    if device.type == "cuda":
        rng["cuda"] = _encode(torch.cuda.get_rng_state(device))
    return {
        "schemaVersion": CHECKPOINT_SCHEMA,
        "currentStep": int(step),
        "modelState": _encode(model.state_dict()),
        "optimizerState": _encode(optimizer.state_dict()),
        "scheduler": {
            "kind": "ExponentialLR-with-fixed-prefix",
            "gamma": float(scheduler.gamma),
            "lastEpoch": int(scheduler.last_epoch),
            "prefixSteps": int(prefix_steps),
            "currentLr": [float(g["lr"]) for g in optimizer.param_groups],
        },
        "batchGeneratorState": _encode(batch_generator.get_state()),
        "order": [int(i) for i in order.detach().cpu().tolist()],
        "cursor": int(cursor),
        "rngStates": rng,
        "seeds": dict(seeds),
        "device": str(device),
        **(dict(extra) if extra else {}),
    }


def model_weights(checkpoint: Mapping[str, Any]) -> dict[str, Any]:
    """The model parameters of a checkpoint in the nested-list form ``model_from_weights`` reads.

    Stored once, read two ways: ``restore`` puts them back into a live model to continue
    training, this returns them as plain nested lists so the ordinary CPU evaluation path can
    score the checkpoint without knowing anything about optimizer state.
    """

    return {name: tensor.tolist() for name, tensor in _decode(checkpoint["modelState"]).items()}


def restore(torch, checkpoint: Mapping[str, Any], model, optimizer, scheduler, *, device) -> dict[str, Any]:
    """Put a captured state back. Returns the bookkeeping the training loop needs."""

    if checkpoint.get("schemaVersion") != CHECKPOINT_SCHEMA:
        raise ValueError(f"checkpoint schema {checkpoint.get('schemaVersion')!r} is not {CHECKPOINT_SCHEMA!r}")
    model.load_state_dict(_decode(checkpoint["modelState"], device=str(device)))
    opt_state = _decode(checkpoint["optimizerState"], device=str(device))
    opt_state["state"] = _int_keys(opt_state["state"])
    optimizer.load_state_dict(opt_state)
    scheduler.gamma = float(checkpoint["scheduler"]["gamma"])
    scheduler.last_epoch = int(checkpoint["scheduler"]["lastEpoch"])
    # The optimizer's own state_dict already carries each group's learning rate; assert it
    # rather than assume it, because a silently reset LR is exactly the kind of thing that
    # makes a "continuation" not one.
    stored = [float(v) for v in checkpoint["scheduler"]["currentLr"]]
    actual = [float(g["lr"]) for g in optimizer.param_groups]
    if stored != actual:
        raise ValueError(f"restored learning rates {actual} are not the stored {stored}")
    scheduler._last_lr = actual                                    # what get_last_lr() reports
    rng = checkpoint["rngStates"]
    torch.set_rng_state(_decode(rng["cpu"]).to(torch.uint8))
    if "cuda" in rng and device.type == "cuda":
        torch.cuda.set_rng_state(_decode(rng["cuda"]).to(torch.uint8), device)
    generator = torch.Generator()
    generator.set_state(_decode(checkpoint["batchGeneratorState"]).to(torch.uint8))
    return {
        "step": int(checkpoint["currentStep"]),
        "order": torch.tensor([int(i) for i in checkpoint["order"]], dtype=torch.long).to(device),
        "cursor": int(checkpoint["cursor"]),
        "batchGenerator": generator,
        "prefixSteps": int(checkpoint["scheduler"]["prefixSteps"]),
    }
