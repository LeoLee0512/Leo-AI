# Leo AI Studio 鈥?Phase 0 鎵ц鐘舵€?

> 渚濇嵁锛歚Leo-AI-Studio-浜у搧鏋舵瀯涓庡墠绔噸鏋勫璁?md`銆乣Leo-AI-Studio-P0鏁存敼娓呭崟.md`
> 鏈枃浠舵槸 Phase 0 鐨勫敮涓€娌荤悊璁板綍銆?
> 鐘舵€佸彛寰勶細`TODO` / `IN_PROGRESS` / `PASS` / `PARTIAL` / `BLOCKED`銆?
> **`NOT TESTED` 姘歌繙涓嶅緱鍐欐垚 `PASS`銆?*

> **Round 2 鏇存柊锛?026-09-03锛?*锛氭帴鍙椾簩娆″鏍告姤鍛婄殑鍒ゅ畾锛屼笉浜夎京娴嬭瘯鏁伴噺銆?
> 涓婁竴杞妸銆屼换鍔¤矾寰勫凡鍒嗗紑銆嶈繃搴︽帹鏂垚銆岃瘉鎹摼鍙俊銆嶏紝`P0-2 = PASS` 鍐欐棭浜嗐€?

| # | 浠诲姟 | layer | Round 1 鑷姤 | 澶嶆牳鍒ゅ畾 | Round 3 鐜扮姸 |
|---|---|---|---|---|---|
| P0-1 | 鍗曚竴鍙俊婧愮爜 | build/tooling | PASS | REOPEN | `PASS` |
| P0-2 | research-sop 璇佹嵁瀹屾暣鎬?| skill | PASS | FAIL | `PASS` |
| P0-3 | Visible UI 涓?ShellApi 涓€鑷?| shell + injection | PASS | CONDITIONAL | `PASS`锛坓ated bridge + mutation test锛?|
| P0-4 | 鍘婚櫎涓汉璺緞缁戝畾 | shell + build/tooling | PARTIAL | PARTIAL | `PARTIAL`锛堥潤鎬佹竻闆讹紱27 椤瑰疄鏈?`NOT TESTED`锛?|
| P0-5 | 鏋勫缓鍙鐜?| build/tooling | TODO | FAIL | `PARTIAL`锛坔ermetic 鍙瀯寤哄彲杩愯锛涙棤 wheelhouse锛?|
| P0-6 | 涓嬩竴闃舵 Gate | 鈥?| FAIL | FAIL | **`FAIL`** |

娴嬭瘯鎬绘暟锛?*284 passed**锛圵indows锛宍.venv/Scripts/python -m pytest tests -q`锛宑ommit 12ceb40锛夈€?

---

## P0-1 鍗曚竴鍙俊婧愮爜 鈥?`PASS`

**闂** 瀹¤绉颁笁浠芥簮鐮佷箣闂存病鏈?canonical source銆?

**root cause锛堜笌瀹¤缁撹涓嶅悓锛屽疄娴嬶級**

1. **`LeoAIStudio-build/` 鍜?`LeoAIStudio/` 閮戒笉鏄?git 浠撳簱銆?* 鍞竴鐨勪粨搴撴槸
   `upstream/OpenAI4S`锛堝浐瀹?`a792c38d9984be428437b548db29baab3322f6dc`锛?026-08-28锛夈€?
   鐪熸鐨?root cause 涓嶆槸銆屽浠芥紓绉汇€嶏紝鑰屾槸 **Leo 鑷繁鐨勪唬鐮佷粠鏈繘鍏ョ増鏈帶鍒?*銆?
2. **`leo-studio-src.zip` 涓嶆槸婧愮爜鍖呫€?* 3355 鏉＄洰閲?3323 鏉℃槸 `upstream/`锛?
   Leo 閮ㄥ垎鍙湁 `theme/`(16) + LICENSES + examples銆?*涓嶅惈 `leo_shell/`銆乣stage/`銆?
   `tools/`銆乣tests/`**锛屽嵆鏁翠釜 Windows 澹虫簮鐮侀兘涓嶅湪閲岄潰銆傚畠鏄?08-31 瀵?*閮ㄧ讲鐩綍**鐨勫揩鐓с€?
3. **閫愭枃浠舵瘮瀵癸細zip 涓病鏈変换浣曠嫭鏈夊唴瀹广€?* 16 涓?theme 鏂囦欢 11 涓€愬瓧鑺傜浉鍚岋紱
   5 涓笉鍚岀殑鍏ㄩ儴鏄?live 鏇存柊銆俙files present only in the zip: none`
   鈫?**涓嶉渶瑕?merge**銆?

**棰濆鍙戠幇** 涓変釜鎶€鑳藉彧瀛樺湪浜庨儴缃茬洰褰曞拰 WSL 鏁版嵁鐩綍锛?*鍚屾牱涓嶅湪鐗堟湰鎺у埗閲?*锛?
涓斾袱鑰呬箣闂撮潬鎵嬪伐澶嶅埗銆傝繖灏辨槸涓婁竴杞€岃 CUDA torch 鐨勪慨澶嶅叾瀹炰粠娌′笂绾裤€嶇殑鍘熷洜锛?
daemon 璇荤殑鏄?`~/.local/share/leo-ai-studio/data/user-skills/`锛學indows 渚ф敼浜嗕笉绠楁暟銆?

**implementation**
- `git init` + `.gitignore` + `.gitattributes`锛涢娆℃彁浜?`8a65838`锛?9 涓枃浠躲€?
- 鐢熸垚鐗╃Щ鍑虹増鏈帶鍒讹細`stage/leo-inject.bundle.js`锛堟瀯寤烘椂鐢?`bundle_theme.py` 閲嶇敓鎴愶級銆?
  `pyi-spec/*.spec`锛圥yInstaller `--specpath` 姣忔鐢熸垚锛屼笖浼氱儰杩涙瀯寤烘満缁濆璺緞锛夈€?
  `dist/`銆乣pyi-work/`銆乣manifests/build-*.json`銆?
- **鎶€鑳界撼鍏?canonical**锛歚skills/` 杩涗粨搴擄紝鏂板 `tools/sync_skills.py`
  鍗曞悜涓嬪彂 `skills/ 鈫?閮ㄧ讲鐩綍 鈫?WSL data/user-skills/`锛宍--check` 鍙娴嬫紓绉汇€?
- 鏂板 `tools/build_manifest.py`锛氳褰?Leo commit / upstream revision / bundle 涓?
  鍚勬簮鏂囦欢 SHA-256 / runtime manifest / toolchain / exe SHA-256 / 姣忎釜鎶€鑳界殑鏂囦欢鍝堝笇銆?
  鍙栦笉鍒扮殑鍊间竴寰嬪啓 `"unknown"`锛屼笉鐚溿€?

**tests** `tools/sync_skills.py --check` 閫氳繃锛涜礋鍚戝鐓э紙浜轰负鏀逛竴涓瓧鑺傦級鑳藉悓鏃?
鎶ュ嚭 windows 涓?wsl 涓や晶婕傜Щ骞朵互闈為浂鐮侀€€鍑恒€?

**result** 浠庝粨搴撳彲浠ヨВ閲婂綋鍓嶅彂甯冪増鏈敱浠€涔堢粍鎴愶細
`leo 8a65838` + `upstream a792c38d` + bundle `b82bf906eaa5bb81` + exe锛堟瘡娆￠儴缃茶褰曪級銆?

**remaining risk** 棣栨鎻愪氦涔嬪墠鐨勫巻鍙蹭笉鍙拷婧€斺€旀棦鎴愪簨瀹烇紝鍙兘浠庣幇鍦ㄥ紑濮嬨€?
**rollback** `git init` 涓嶆敼鍔ㄤ换浣曟棦鏈夋枃浠讹紱鍒犻櫎 `.git/` 鍗冲彲鎾ら攢銆?

---

## P0-2 research-sop 璇佹嵁涓查 鈥?Round 1 璁板綍锛堝垽瀹氳涓嬫柟 Round 2 鑺傦級

**layer** skill锛坄skills/research-sop/kernel.py`锛?

**root cause锛堣鐮佺‘璁わ紝鍥涙潯鐙珛缂洪櫡锛?*

1. **闃舵璺緞娌℃湁浠诲姟缁戝畾**锛歚sop_stage_path(role)` 鍥哄畾杩斿洖
   `research-sop/01-literature-surveyor.json`锛屼笉鍚?run id / task hash銆?
   `resume=True`锛?*榛樿鍊?*锛夊洜姝ゆ妸浠诲姟 A 鐨勯樁娈靛綋浣滀换鍔?B 鐨勭粨鏋溿€?
2. **`status` 纭紪鐮?`complete`**锛氬嚱鏁版湯灏炬棤鏉′欢杩斿洖锛屼笌鏄惁鍙窇浜嗗瓙闆嗘棤鍏炽€?
3. **`validator` 纭紪鐮?`pass`**锛歷alidator 鏍规湰娌¤繘 pipeline 涔熸姤 pass銆?
4. **`paper` 璺緞纭紪鐮?*锛歱aper-writer 娌¤窇涔熻繑鍥炶矾寰勶紝鎸囧悜涓嶅瓨鍦ㄧ殑鏂囦欢銆?

**棰濆鍙戠幇** 浠撳簱涓?*涓嶅瓨鍦ㄤ换浣?skill 娴嬭瘯**锛坄tests/` 鍙湁 `leo_shell/` 涓?
`test_package_contract.py`锛夈€傛鍓嶆姤鍛婃彁鍒扮殑銆?4 椤规墦妗╂祴璇曘€嶅湪鏈粨搴撲笉瀛樺湪锛?
鍥犳鏈」鏄?*浠庨浂寤虹珛**娴嬭瘯鑴氭墜鏋躲€?

**瀹炴祴澶嶇幇锛堝 `docs/rollback/research-sop-kernel.pre-P0-2.py`锛?*

```
task A: complete | delegate calls: 5
task B: complete | delegate calls: 0      鈫?B 缁ф壙浜?A 鐨勫叏閮ㄤ簲涓樁娈?
task B validator: pass | paper: research-sop/05-paper-writer.md

subset run (modeler only): status=complete  validator=pass  paper=<path>
```

**implementation**
- 姣忔杩愯鐙珛鐩綍 `research-runs/<run_id>/`锛宍run_id` 鐢?task 鏂囨湰鐨?SHA-256 鎺ㄥ嚭銆?
- `manifest.json`锛歚schema_version` / `run_id` / `task_text` / `task_sha256` /
  `pipeline_version` / `role_order` / `role_prompt_hashes` / `model_fingerprint` /
  `created_at` / `parent_run_id` / `rollbacks`銆?
  妯″瀷韬唤鍙栦笉鍒版椂鍐?`"unknown"` 骞惰鏄庡師鍥狅紝涓嶇紪閫犮€?
- Resume 瑙勫垯锛歵ask hash 鐩稿悓鎵嶅師浣嶇画璺戯紱涓嶅悓涓€瀹氭柊寤?run锛?
  `resume=False` = 鏄庣‘閲嶅仛 鈫?**鏂板缓 run 骞惰 `parent_run_id`锛屾棫 run 鍘熸牱淇濈暀**
  锛堝垹鏃ц瘉鎹瓑浜庢瘉瀹¤閾撅級銆俶anifest 琚敼鍧?鈫?鎶涢敊鎷掔粷澶嶇敤锛屼笉闈欓粯銆?
- 闃舵璁板綍鍐呭祵 `run_id` + `task_sha256`锛宍sop_read_stage` 鍙岄噸鏍￠獙鈥斺€?
  鍗充娇鏈夋父绂绘枃浠惰惤杩?run 鐩綍涔熻涓嶆垚璇佹嵁銆?
- 鐘舵€佽瘹瀹炲寲锛歚complete` / `partial` / `unresolved` / `blocked`锛?
  `validator` 娌＄湡璺戝氨鏄?`None`锛沗paper` 娌＄湡鍐欏氨鏄?`None`銆?
- **娌℃湁淇濈暀浠讳綍鍥為€€鍒版棫鍥哄畾璺緞鐨勫吋瀹瑰垎鏀?*锛堥偅姝ｆ槸姹℃煋婧愶級銆?
- 瑙掕壊鎻愮ず璇嶉噷鍚屾椂琛ヤ簡瀹為獙鐜绾﹀畾锛堜紭鍏堥瑁呯瀛︽爤锛泃orch 蹇呴』 CPU wheel锛?
  瀹佸彲闄嶇骇瀹為獙涔熶笉鍋滀笅鏉ヨ鍑犱釜 GB锛夈€?

**tests** `tests/skills/test_research_sop.py` 鈥?**12 passed**锛岃鐩栨竻鍗曡姹傜殑
Case A鈥揈锛屽彟鍔?manifest 瀛楁銆佽法浠诲姟璇绘嫆缁濄€乼ask hash 褰掍竴鍖栥€佸潖 manifest 鎷掔粷銆?
blocked 鐘舵€併€?*宸查獙璇佽繖浜涙祴璇曞淇鍓嶇殑 kernel 浼氬け璐?*锛堣涓婃柟澶嶇幇锛夛紝
涓嶆槸绌鸿浆鐨勬祴璇曘€?

**remaining risk** 鏃х殑 `research-sop/` 鍥哄畾璺緞閬楃暀鏂囦欢浠嶅湪浼氳瘽宸ヤ綔鍖洪噷锛?
鏂颁唬鐮佷笉浼氳瀹冧滑锛堣矾寰勪笉鍚岋級锛屼絾涔熸病鏈変富鍔ㄦ爣璁颁负 legacy銆?
**rollback** `docs/rollback/research-sop-kernel.pre-P0-2.py`

---

## P0-2 Round 2锛氳矾寰勫垎寮€ 鈮?璇佹嵁鍙俊

澶嶆牳鎶ュ憡鐨勬牳蹇冩壒璇勬垚绔嬶細涓婁竴杞彧瑙ｅ喅浜嗚韩浠界粦瀹氾紝娌¤В鍐崇姸鎬佸彲淇°€乻chema 鍙俊銆?
artifact 鐪熷疄銆佸巻鍙蹭笉鍙彉銆佺増鏈吋瀹瑰拰璺緞瀹夊叏銆?*鎴戠嫭绔嬪鐜颁簡瀹冩寚鍑虹殑涓绘紡娲?*锛?

```
first = orchestrate_research(TASK_A)          # 姝ｅ父瀹屾垚
files[manifest_path] = "{ this is not json"   # manifest 鎹熷潖浣嗗瓨鍦?
orchestrate_research(TASK_A, resume=True)
鈫?status: complete | delegate calls: 0        # 闈欓粯閲嶅缓 manifest锛屾棫闃舵琚綋浣滆瘉鎹?
```

涓婁竴杞垜鍦ㄦ湰鏂囦欢閲屽啓鐨勩€宮anifest 琚敼鍧?鈫?鎶涢敊鎷掔粷澶嶇敤銆?*鏄敊鐨?*锛氶偅鏉″彧瑕嗙洊
銆孞SON 鍚堟硶浣?task hash 涓嶇銆嶏紝鑰屼笉鏄€孞SON 鏈韩鎹熷潖銆嶃€傚凡鏇存銆?

涔濈被淇锛堝搴斿鏍告姤鍛?搂5.1鈥?.10锛夛細

| # | 婕忔礊 | 淇 |
|---|---|---|
| 1 | 鎹熷潖 manifest 琚綋浣滀笉瀛樺湪 | 鍥涙€?`missing/valid/corrupt/incompatible`锛沜orrupt **fail closed**锛屽師瀛楄妭涓嶈鐩?|
| 2 | 缂?`run_id`/`task_sha256` 鐨?stage 浠嶈鎺ュ彈 | 绮剧‘鐩哥瓑锛宍None` 涓嶅啀绠楀尮閰嶏紱`role` 涔熻瀵逛笂 |
| 3 | delegate 澶辫触浠嶈 complete | 妫€鏌?`task_status`/`error`/`stop_reason`锛屽師濮?payload 淇濈暀 |
| 4 | schema 鍙紶缁?host锛屼笉澶嶆牳 | orchestrator 鍐呮湰鍦板鏍?required keys + verdict 鏋氫妇 |
| 5 | paper 璺緞鍙兘鎸囧悜涓嶅瓨鍦ㄧ殑鏂囦欢 | 鏂囨。蹇呴』瀛樺湪涓旈潪绌猴紝璁?`document_sha256` |
| 6 | rollback 鐢ㄧ┖涓茶鐩栬瘉鎹?| 褰掓。鍒?`history/rollback-NNN/`锛岃鍥炴牎楠屽悗鎵嶆竻绌猴紱澶辫触鍗充腑姝?|
| 7 | roles 鍏佽涔卞簭閲嶅 | 蹇呴』鏄?`ROLE_ORDER` 鐨勫敮涓€淇濆簭瀛愬簭鍒?|
| 8 | `run_id`/suffix 鍙矾寰勭┛瓒?| strict fullmatch + suffix 鏋氫妇 + 瑙勮寖鍖栧悗 containment 妫€鏌?|
| 9 | prompt/pipeline 鍙樺寲琚潤榛樺鐢?| 鍙備笌 resume 鍒ゅ畾锛涢粯璁?fork 鏂?run 璁?`parent_run_id`锛屽彲璁?`on_incompatible="fail"` |
| 10 | resume 姘歌繙鍥炲埌 base 鍒嗘敮 | 榛樿缁窇**鏈€鏂板垎鏀?*锛屾敮鎸佹樉寮?`run_id=`锛宍sop_run_lineage()` 鍙洖婧?|

**娴嬭瘯**锛歚tests/skills/test_research_sop_integrity_adversarial.py`锛?1 椤癸級銆?
澶嶆牳鏂圭殑鍘熷鏂囦欢琚彁鍙婁絾**鏈殢闄?*锛屾墍浠ヨ繖鏄寜鎶ュ憡 搂2.4/搂5 鐨勬弿杩?*鐙珛閲嶅缓**鐨勭増鏈紱
浠栦滑鐨勬枃浠跺埌浜嗗簲褰撲竴骞惰窇锛岃€屼笉鏄浛鎹€?

**璇佹嵁**锛氳繖 41 椤归噷 **32 椤瑰 round-1 kernel 澶辫触**銆佸叏閮ㄥ褰撳墠 kernel 閫氳繃銆?
涓嶆槸绌鸿浆鐨勬祴璇曘€傦紙`docs/rollback/research-sop-kernel.pre-P0-2-round2.py` 淇濈暀浜?round-1 鐗堟湰渚涘楠屻€傦級

**涓ゅ鎴戝垽瀹氬鏍告柟鎻忚堪闇€瑕佷慨姝ｇ殑**锛堝凡鍦ㄦ祴璇曟敞閲婁腑璇存槑锛夛細
- 銆宲aper 鏂囨。琚垹鍚庡繀椤昏繑鍥?`paper=None`銆嶁€斺€旀纭涓烘槸**閲嶈窇璇ラ樁娈?*骞朵骇鍑虹湡瀹炴枃妗ｏ紝
  娴嬭瘯鏂█鐨勬槸銆屽繀椤婚噸璺戙€嶈€屼笉鏄€屽繀椤诲彉 None銆嶏紱
- 銆宲rompt 鏀瑰彉鍚庢棫 run 浠嶅彲 `sop_read_manifest`銆嶁€斺€旀棫 run 鍦ㄦ柊 prompt 涓嬫湰灏变笉鏄?
  *valid* manifest锛屾纭柇瑷€鏄畠琚垎绫讳负 `incompatible` 涓斿瓧鑺備粛鍦ㄣ€?

---

## P0-1 Round 2锛氬彂甯冮『搴忎笌 strict verifier

澶嶆牳鎶ュ憡 搂4 鐨勬寚鎺ф垚绔嬩笖鍙鐜般€傛柊澧?`tools/verify_release.py` 鍚庯紝瀵逛笂涓€杞殑
manifest 杩愯锛?*閫愭潯澶嶇幇浜嗘姤鍛婇噷寮曠敤鐨勫悓涓€缁勫搱甯?*锛?

```
leo commit      FAIL  manifest 8a65838f33e7 != HEAD 6596cfbf59e0
source hashes   FAIL  unified-settings-adapter.js 41df7e19429b!=1f479736c455
                      stage/leo-inject.js         3dd7a177b8ed!=3bf82d3739b4
deployed bundle FAIL  deployed exe FAIL  skill hashes FAIL
```

verifier 妫€鏌ワ細manifest commit == git HEAD銆乺epo clean銆佹簮鏂囦欢鍝堝笇銆侀儴缃?bundle銆?
閮ㄧ讲 EXE銆乧anonical skill 鍝堝笇銆侀儴缃蹭笌 WSL daemon 鍓湰涓€鑷淬€乽pstream 鍥哄畾 revision
锛堟柊澧?`manifests/upstream-pin.json`锛夈€乽pstream 宸ヤ綔鏍戝共鍑€銆?
`--strict` 涓?**NOT TESTED 涔熺畻澶辫触**锛岀粷涓嶅苟鍏?PASS銆?

---

## P0-3 Visible UI 涓?ShellApi 涓€鑷?鈥?`PASS`锛圧ound 3 鎻愬崌锛岃涓嬶級

**root cause锛堣嚜鍔ㄦ壂鎻忕‘璁わ級** 11 涓柟娉曡鍓嶇璋冪敤浣嗗湪
`leo_shell/api.py:_UNIMPLEMENTED_EXTENSIONS` 閲岋紝鍏ㄩ儴鏉ヨ嚜 `stage/leo-inject.js`锛?

| 缁?| 鏂规硶 | 瀹¤缁欑殑浼樺厛绾?|
|---|---|---|
| 鏁版嵁鐢熷懡鍛ㄦ湡 | `list_entity_states` `mark_entity` `restore_entity` `forget_entity` | 1 |
| 椤圭洰 Persona | `get_project_persona` `save_project_persona` | 2 |
| 鑷畾涔変富棰?| `choose_theme_file` `stage_theme_preview` `confirm_theme_preview` `discard_theme_preview` `delete_custom_theme` | 3 |

`called but absent entirely: []`銆乣declared-unimpl and never called: []` 鈥斺€?娌℃湁绗洓绫婚棶棰樸€?

**implementation** 鎸夈€屼笉瑕佷负浜嗕繚浣忔棫 UI 鑰屼复鏃跺疄鐜板ぇ閲忎綆浼樺厛绾?API銆嶏細
- `LEO_FEATURE_FLAGS`锛坄entityLifecycle` / `projectPersona` / `customThemes`锛屽叏 `false`锛夈€?
- **markup 鍦?flag 涓?false 鏃舵牴鏈笉娓叉煋**锛屼笉鏄覆鏌撳悗鍐?disable 鈥斺€?
  銆岀偣浜嗘墠璇存殏鏈疄鐜般€嶇殑浼叆鍙ｈ绉婚櫎鑰屼笉鏄彉鐏般€?
- `data` 椤垫暣椤垫棤鍚庣 鈫?杩炲鑸爣绛鹃兘涓嶇粰锛坅dapter 鏂板 `hiddenPages`锛?
  鍚屾椂璁?`resolvePage()` 鏃犳硶瑙ｆ瀽鍒伴殣钘忛〉锛宍openCust("data")` 鍥炶惤鍒伴粯璁ら〉锛夈€?
- `memory` 椤?*淇濈暀**锛氬彧闅愯棌 Leo 鐨?persona 鍧楋紝璇ラ〉鐨勪笂娓告覆鏌撳櫒浠嶇劧宸ヤ綔鈥斺€?
  鏁撮〉闅愯棌浼氳繛甯︾爫鎺夎兘鐢ㄧ殑涓婃父鍔熻兘銆?
- 瀵瑰簲鐨?`addEventListener` / 鏂囨璧嬪€煎悓鏍疯繘 flag锛屽惁鍒?`querySelector(...)` 杩斿洖
  null 浼氭姏寮傚父銆?

**tests** `tests/test_ui_api_contract.py` 鈥?**5 passed**銆傛妸 flag 鎵撳紑浼氱珛鍒诲け璐?
锛堣礋鍚戝鐓у疄娴嬶細2 failed锛夛紝鎵€浠ャ€屾墦寮€ flag銆嶇瓑浜庛€屽繀椤诲厛瀹炵幇鍚庣銆嶃€?
鏂板鏈疄鐜版柟娉曞嵈涓嶆寚瀹氬綊灞?flag 涔熶細澶辫触銆?

**remaining risk** 闅愯棌涓嶇瓑浜庡疄鐜般€傛暟鎹敓鍛藉懆鏈熸槸瀹¤缁欑殑绗竴浼樺厛锛?
搴斿湪 Phase 1 棣栧厛琛ラ綈銆?*娉ㄦ剰**锛氶」鐩?/ 浼氳瘽 / 浜х墿鐨勫垹闄ゅ凡缁忛€氳繃涓婃父鑷繁鐨?
`deleteProject` / `deleteSession` / `deleteArtifact` 琛ヤ笂浜嗗叆鍙ｏ紝涓庤繖閲岀殑
Leo 涓撳睘 entity lifecycle 鏄袱浠朵簨銆?

---

## P0-4 鍘婚櫎涓汉璺緞缁戝畾 鈥?`PARTIAL`

**宸叉竻闄?*
- `pyi-spec/LeoAIStudio.spec`锛? 澶勭粷瀵硅矾寰勶級锛氱‘璁ょ敱 PyInstaller `--specpath`
  姣忔鐢熸垚锛屽睘浜庝骇鐗?鈫?绉诲嚭鐗堟湰鎺у埗骞跺姞鍏?`.gitignore`銆?
- `tools/make_lion_icon.py`锛? 澶勶級锛氭敼涓轰粨搴撶浉瀵?+ `LEO_APP_ROOT` 瑕嗙洊銆?
- `tools/sync_skills.py`锛? 澶勶級锛氭敼涓?`LEO_WSL_DISTRO` / `LEO_WSL_USER` /
  `LEO_WSL_SKILLS` 鐜鍙橀噺锛岄粯璁ゅ€肩敱鐢ㄦ埛鍚嶆帹瀵笺€?

**浠嶆湭娓呴櫎锛坄TODO`锛?*
- `skills/lean-math/kernel.py` **5 澶?* `/home/leo/...`锛歀ean toolchain銆?
  lake銆乣lean_test` 宸ョ▼銆乣mathlib4` 鐩綍锛屼笖鍐欐 RC 鐗堟湰
  `leanprover--lean4---v4.34.0-rc2`銆傞渶瑕佺殑鏄?*鑷姩鍙戠幇 + health check + 鏄惧紡閰嶇疆**
  锛堟寜鎸囩ず鏈疆涓嶉噸鏋勬暣涓?Lean 闆嗘垚锛夈€?
- 瀹夎鐩綍涓庣敤鎴锋暟鎹洰褰曞皻鏈垎绂伙紙浠嶆槸 `Desktop\LeoAIStudio\` 涓嬫贩鏀撅級銆?
- 蹇嵎鏂瑰紡浠嶇敱 `deploy_release.ps1` 鎸囧悜鍥哄畾妗岄潰鐩綍锛屾病鏈夊畨瑁呭櫒銆?

**楠屾敹鐘舵€侊細`NOT TESTED`銆?* 銆屽湪鍏ㄦ柊 Windows 璐︽埛涓畨瑁呭苟鍚姩銆?*鏃犳硶鍦ㄦ湰鐜鑷瘉**鈥斺€?
鎴戜笉鑳藉垱寤?Windows 鐢ㄦ埛璐︽埛銆備互涓嬮」鐩?*蹇呴』鐢变汉宸ョ幇鍦洪獙鏀?*锛屼笉寰楄涓洪€氳繃锛?

1. 鏂拌处鎴蜂笅鍙屽嚮蹇嵎鏂瑰紡鑳藉惎鍔紝涓斾笉闇€瑕佹敼浠讳綍璺緞锛?
2. WebView2 鍥哄畾鐗堣繍琛屾椂鍦ㄦ柊璐︽埛涓嬪彲鍔犺浇锛?
3. WSL2 鍙戣鐗堝悕绉?/ 鐢ㄦ埛鍚嶄笉鏄?`Ubuntu-24.04` / `leo` 鏃舵ˉ鎺ユ槸鍚︿粛宸ヤ綔锛?
4. Lean 鍦ㄦ病鏈?`/home/leo/...` 鐨勬満鍣ㄤ笂鐨勮涓恒€?

---

## P0-5 鏋勫缓鍙鐜?鈥?`TODO`

鏈紑濮嬨€傚凡鐭ヤ簨瀹烇細`tools/build_launcher.ps1` 浠嶄粠鏃㈡湁 `LeoAIStudio.exe` /
`_launcher` 涓庢棫 PYZ 鍙嶅悜鎻愬彇渚濊禆锛堝璁?搂9.2锛夈€傞渶瑕佷緷璧栭攣 + wheelhouse +
鏋勫缓 manifest锛坢anifest 閮ㄥ垎宸茬敱 `tools/build_manifest.py` 鎻愬墠鍏峰锛夈€?

---

## Round 3锛?C + 2D锛?

### 2C 鈥?P0-3 浠?`CONDITIONAL PASS` 鎻愬崌鍒?`PASS`

澶嶆牳鏂圭殑 mutation test 鏄鐨勩€傛垜澶嶇幇浜嗭細鍦?`leo-inject.js` 鏈熬杩藉姞涓€鏉℃湭缁?gate 鐨?
`window.pywebview.api.list_entity_states({});`锛屽師鏉ョ殑 5 椤?UI 濂戠害娴嬭瘯**鍏ㄩ儴鐓у父閫氳繃**銆?
瀹冧滑鏂█鐨勬槸銆宖lag 鐨勫€兼槸 false銆嶏紝閭ｆ槸涓€涓€硷紝涓嶆槸鍙揪鎬с€?

鐜板湪娉ㄥ叆灞傚彧閫氳繃涓€涓嚱鏁拌Е杈惧澹筹細`leoBridge(method, ...)`锛屽畠鍦?feature 鍏抽棴鏃剁洿鎺ユ姏閿欍€?
19 澶勮皟鐢ㄧ偣鍏ㄩ儴鏀瑰啓锛堝惈涓ゅ鎶婃柟娉曞綋鍊间紶鐨勶細涓婚棰勮 confirm/discard銆?
`acknowledge_connection` 瀛樺湪鎬ф帰娴嬶級銆?*瀛楅潰閲?`pywebview.api.<name>` 鍦ㄦ敞鍏ュ眰琚姝?*锛?
濂戠害娴嬭瘯鍙戠幇鍗冲け璐ャ€?

瀹炴祴 mutation锛氬共鍑€ `10 passed` 鈫?杩藉姞鏈?gate 璋冪敤 `2 failed` 鈫?鎾ら攢 `10 passed`銆?
鎵€浠ャ€屽叧闂€嶇幇鍦ㄧ瓑浜庛€岃皟涓嶅埌銆嶏紝鑰屼笉鏄€屾病娓叉煋鎸夐挳銆嶃€?

`shell.html` 鍒绘剰涓嶈蛋 bridge锛氬畠鏄惎鍔ㄩ〉锛屾病鏈変换浣?gated 鍔熻兘锛屽崟鐙柇瑷€瀹冨彧璋冨凡瀹炵幇鏂规硶銆?

### 2D-A 鈥?P0-4 闈欐€侀儴鍒嗘竻闆讹紝瀹炴満閮ㄥ垎鍏ㄩ儴 `NOT TESTED`

- `lean-math` 鐨?5 澶?`/home/leo/...` 涓庡啓姝荤殑 RC 宸ュ叿閾惧叏閮ㄧЩ闄ゃ€傝В鏋愰『搴忥細
  閰嶇疆锛坄LEO_LEAN_TOOLCHAIN` / `LEO_LEAN_PROJECT` / `LEO_MATHLIB_DIR`锛夆啋 home 涓嬬殑 elan
  鈫?PATH 涓婄殑 `lean`/`lake`銆俙lean_toolchain_status()` 杩斿洖
  `READY` / `NOT_INSTALLED` / `PROJECT_NOT_READY` / `VERSION_MISMATCH` 骞堕檮鍙搷浣滆鏄庯紝
  **浠讳綍鎯呭喌涓嬮兘涓嶈嚜鍔ㄥ畨瑁?*銆?
- `deploy_release.ps1` 鍘熸湰鏂█涓€鏉″瓧闈㈤噺瀹夎璺緞銆傚畧鍗繚鐣欙紙閮ㄧ讲鍒伴敊鐩綍鏄牬鍧忔€х殑锛夛紝
  浣嗘敼涓?*鎸夌粨鏋勫垽鏂?*鐩爣鏄笉鏄竴涓?Leo 瀹夎锛岃€屼笉鏄垽鏂畠鍦ㄨ皝鐨勬闈笂銆?
- 鍙︽竻闄わ細`build_launcher` 鐨勫浐瀹氫复鏃剁洰褰曘€乣capture_window` 鐨勮緭鍑鸿矾寰勩€?
  `headless_verify` 鐨勯粯璁ゆ牴銆乣make_lion_icon` 鏂囨。閲岀殑瑙ｉ噴鍣ㄣ€?
- `tools/portability_check.py`锛?*0 hard binding锛? configurable default**銆?
  `tests/test_portability.py` 鎶婂畠绾冲叆娴嬭瘯骞跺甫璐熷悜瀵圭収銆?
- **闈欐€侀€氳繃 鈮?瀹炴満閫氳繃銆?* `docs/P0_MANUAL_ACCEPTANCE_CHECKLIST.md` 鍒楀嚭 27 椤规棤娉曡嚜璇佺殑
  瀹炴満楠屾敹锛?*鍏ㄩ儴 `NOT TESTED`**銆傚洜姝?P0-4 = `PARTIAL`銆?

### 2D-B 鈥?P0-5 浠?`TODO` 鍒?`PARTIAL`

浜斿瀵规棫鍙戝竷浠剁殑渚濊禆鍏ㄩ儴绉诲埌 `-Legacy` 寮€鍏充箣鍚庯紝hermetic 鎴愪负榛樿銆?
`requirements.lock` 鍥哄畾 21 涓寘锛宍manifests/dependency-lock.json` 璁板綍鏉ユ簮
骞?*鏄庡啓 `vendored_wheelhouse: false`**銆?

璺戝嚭鏉ョ殑涓や釜缁撹锛堜笉鏄帹鏂級锛?

- **PYZ 鎻愬彇纭疄鏄浣欑殑**锛氬畠鎭㈠鐨勫叚涓ā鍧楀湪姝ｅ父鏋勫缓鐨?PYZ 閲岄兘鏈夛紝
  `webview` 鐨?45 涓ā鍧椾篃鍦ㄣ€傛棫 `_launcher` 閲岀殑鏁ｈ鍓湰鏄啑浣欏洖濉€?
- **鍥炲～涓嶆槸澶氫綑鐨?*锛屽畠鍦ㄦ帺鐩栫己澶辩殑鍘熺敓 DLL銆傝繖涓?Python 鏄?conda 鍙戣鐗堬紝
  `ffi-8.dll` / `sqlite3.dll` / `libbz2.dll` / `liblzma.dll` / `libexpat.dll` 鏀惧湪
  `<base_prefix>/Library/bin`锛孭yInstaller 涓嶆壂閭ｉ噷銆?*绗竴娆?hermetic 鏋勫缓閫氳繃浜?
  package contract锛岀劧鍚庡惎鍔ㄦ椂姝诲湪 `DLL load failed while importing _ctypes`銆?*
  鐜板湪杩欎簺 DLL 鏉ヨ嚜澹版槑鐨?Python 宸ュ叿閾俱€?

**楠岃瘉鏂瑰紡**锛氭妸 hermetic 浜х墿鏀捐繘涓€涓?scratch 瀹夎鏍戯紝璺?`--diagnostics`锛?
**exit 0 骞跺啓鍑烘姤鍛?* 鈥斺€?璇存槑鐪熷疄 import 鍥惧湪銆岄浂鏃у彂甯冧欢杈撳叆銆嶇殑鏋勫缓閲岃兘鍔犺浇銆?

**涓轰粈涔堜粛鏄?`PARTIAL` 鑰屼笉鏄?`PASS`**锛氭病鏈?vendored wheelhouse锛坵heel 浠嶄粠 PyPI 瑙ｆ瀽锛夛紝
涓斻€屽湪涓€鍙颁粠鏈杩囨棫鐗堢殑鏈哄櫒涓?clean build銆嶅睘浜庡疄鏈洪獙鏀堕」锛屾湭鍋氥€?

---

## P0-6 Gate 鈥?`FAIL`

涓婁竴鐗堣繖閲屽啓銆孭0-1 / P0-2 / P0-3 宸叉竻闆躲€嶏紝涓庤〃澶寸殑
`P0-3 = CONDITIONAL PASS` 鑷浉鐭涚浘銆傜煕鐩剧殑鏉ユ簮鏄彊浜嬮『鎵嬶紝涓嶆槸浜嬪疄鍙樺寲锛屽凡鏇存銆?

Gate 鐜扮姸锛堝彛寰勫彧鍏佽 `PASS` / `FAIL` / `PARTIAL` / `BLOCKED` / `NOT TESTED`锛夛細

| Gate 蹇呴』椤?| 鐘舵€?|
|---|---|
| P0-1 鍗曚竴鍙俊婧愮爜 | `PASS` |
| P0-2 research-sop 璇佹嵁瀹屾暣鎬?| `PASS` |
| P0-3 Visible UI 涓?ShellApi 涓€鑷?| `PASS` |
| P0-4 鍙Щ妞嶆€?| `PARTIAL` 鈥?闈欐€佹竻闆讹紝27 椤瑰疄鏈洪獙鏀?`NOT TESTED` |
| P0-5 鏋勫缓鍙鐜?| `PARTIAL` 鈥?hermetic 鍙瀯寤哄彲杩愯锛屾棤 wheelhouse锛宑lean-machine 鏋勫缓鏈獙 |

**鍙鍏朵腑浠讳綍涓€椤逛笉鏄?`PASS`锛孭0-6 灏辨槸 `FAIL`銆?*
`CONDITIONAL PASS` 涓嶇畻 `PASS`锛沗NOT TESTED` 涓嶇畻 `PASS`銆?
鍥犳鐜板湪涓嶅緱杩涘叆 Workspace / PINN / Companion / 鏂板墠绔姛鑳姐€?

---

## 鍙樻洿鏃ュ織

| 鏃堕棿 | 鍐呭 |
|---|---|
| 2026-09-03 | 寤虹珛鏈枃浠讹紱瀹屾垚 P0-1 浜嬪疄璁ゅ畾锛堟棤鐗堟湰鎺у埗 / zip 闈炴簮鐮佸寘 / 鏃犻渶 merge锛?|
| 2026-09-03 | P0-2锛歳un 缁戝畾 + manifest + 鐘舵€佽瘹瀹炲寲锛?2 椤瑰洖褰掓祴璇曪紝宸插淇鍓?kernel 楠岃瘉浼氬け璐?|
| 2026-09-03 | P0-3锛氫笁缁?feature flag锛宍data` 椤电Щ鍑哄鑸紝5 椤瑰绾︽祴璇?+ 璐熷悜瀵圭収 |
| 2026-09-03 | P0-4锛氭竻闄?spec / 涓や釜宸ュ叿鐨勭‖缂栫爜锛沴ean-math 涓庡畨瑁呭竷灞€浠嶅緟鍔?|
| 2026-09-03 | 棣栨鎻愪氦 `8a65838`锛涙瀯寤?+ 閮ㄧ讲锛屽绾﹂€氳繃锛?43 tests passed |

