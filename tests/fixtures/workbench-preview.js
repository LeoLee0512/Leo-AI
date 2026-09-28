/* Visual/interaction fixture only. Never bundled or used as scientific evidence. */
(() => {
const project={id:'p-preview',project_id:'p-preview',name:'科学计算与探索'};
let frames=[{id:'f-poisson',project_id:project.id,name:'一维 Poisson：从边值问题到误差验证',updated_at:'2026-09-26T10:00:00Z'},
{id:'f-heat',project_id:project.id,name:'热传导模型中的边界条件',updated_at:'2026-09-25T10:00:00Z'},
{id:'f-notes',project_id:project.id,name:'关于 PINN 收敛与残差的几个问题',updated_at:'2026-09-24T10:00:00Z'}];
let task;
const messages={};
window.pywebview={api:{
  workbench_request:async p=>{
    let data={};
    if(p.operation==='projects')data={projects:[project]};
    else if(p.operation==='frames')data={frames};
    else if(p.operation==='create_frame'){data={id:'f-'+Date.now(),project_id:project.id};frames.unshift(data);}
    else if(p.operation==='frame')data=frames.find(f=>f.id===p.frameId);
    else if(p.operation==='messages')data={messages:messages[p.frameId]||[{message_id:'m-1',seq:0,role:'user',content:'为什么边界条件对 Poisson 问题的唯一性很重要？'},{message_id:'m-2',seq:1,role:'assistant',content:'边界条件限定了允许的解空间。对于一维 Poisson 问题，给定两个端点的 Dirichlet 条件，就可以排除齐次方程中任意的线性项。\n\n**下一步**\n我们可以先写出方程与边界条件，再用参考解核对离散误差。\n\n这是界面预览内容，不是科学计算结果。'}],has_earlier:false};
    else if(p.operation==='execution')data={owner:null,queue:[]};
    else if(p.operation==='send'){messages[p.frameId]=[{message_id:'user-new',seq:0,role:'user',content:p.text},{message_id:'assistant-new',seq:1,role:'assistant',content:'收到。此回复仅用于界面交互检查。'}];data={status:'accepted'};}
    else if(p.operation==='rename'){const f=frames.find(f=>f.id===p.frameId);f.name=p.name;data=f;}
    else if(p.operation==='notebook')data=p.frameId==='f-poisson'?{total:2,omitted:0,entries:[
      {ordinal:1,cellIndex:1,language:'python',status:'ok',source:"import numpy as np\nx = np.linspace(0, 1, 201)\nu_exact = np.sin(np.pi * x)\nprint(f'grid points: {x.size}')",stdout:'grid points: 201\n',stderr:'',error:'',truncated:false,figures:[],filesWritten:[],attempt:1,attemptCount:1,latest:true,stale:false,cpuSeconds:0.04},
      {ordinal:2,cellIndex:2,language:'python',status:'ok',source:"err = np.abs(u_pinn - u_exact)\nprint(f'relative L2 = {np.linalg.norm(err)/np.linalg.norm(u_exact):.3e}')\nplt.plot(x, err); plt.savefig('pointwise_error.svg')\nnp.savetxt('pointwise_error.csv', np.c_[x, err], delimiter=',')",stdout:'relative L2 = 2.552e-04\n',stderr:'',error:'',truncated:false,figures:['pointwise_error.svg'],filesWritten:['pointwise_error.svg','pointwise_error.csv'],attempt:2,attemptCount:2,latest:true,stale:false,cpuSeconds:1.37}]}:{total:0,omitted:0,entries:[]};
    else if(p.operation==='feedback')data={feedback:window.__previewFeedback||(window.__previewFeedback={})};
    else if(p.operation==='set_feedback'){const fb=window.__previewFeedback||(window.__previewFeedback={});if(p.rating)fb[p.key]=p.rating;else delete fb[p.key];data={ok:true};}
    else if(p.operation==='kernel')data={state:p.frameId==='f-poisson'?'running':'none',alive:p.frameId==='f-poisson',generation:1};
    else if(p.operation==='artifacts')data={artifacts:p.frameId==='f-poisson'?[{id:'a-preview0001',filename:'pointwise_error.svg',contentType:'image/svg+xml',size:2048,createdAt:'2026-09-26T10:02:00Z',upload:false},{id:'a-preview0002',filename:'pointwise_error.csv',contentType:'text/csv',size:5120,createdAt:'2026-09-26T10:02:00Z',upload:false}]:[]};
    else if(p.operation==='artifact_preview'){
      if(p.artifactId==='a-preview0002')data={id:p.artifactId,filename:'pointwise_error.csv',kind:'text',contentType:'text/csv',size:5120,truncated:false,text:'x,err\n0.000,0.000e+00\n0.005,1.8e-05\n0.010,3.4e-05\n0.015,4.9e-05\n…'};
      else{let d='M40 150';for(let i=0;i<=100;i++){const x=i/100;d+=' L'+(40+x*320).toFixed(1)+' '+(150-110*Math.abs(Math.sin(3*Math.PI*x))*x*(1-x)*4).toFixed(1);}
        const svg='<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 180"><rect width="400" height="180" fill="#fff"/><path d="M40 20V150H370" stroke="#594B3C" fill="none"/><path d="'+d+'" stroke="#9C3A28" stroke-width="2" fill="none"/><text x="44" y="16" font-size="11" fill="#594B3C">|u_PINN - u| (preview)</text></svg>';
        data={id:p.artifactId,filename:'pointwise_error.svg',kind:'image',contentType:'image/svg+xml',size:2048,dataUri:'data:image/svg+xml;base64,'+btoa(svg)};}
    }
    return {ok:true,data};
  },
  list_entity_states:async()=>({ok:true,entities:[]}),
  list_session_models:async()=>({ok:true,binding:{profile_id:'mp-preview',revision:1,native_profile_id:'preview'},active_native_profile_id:'preview',models:[{id:'preview',name:'DeepSeek',model:'deepseek-v4-pro',available:true}]}),
  select_session_model:async()=>({ok:true,binding:{profile_id:'mp-preview',revision:1,native_profile_id:'preview'}}),
  get_state:async()=>({profiles:[{name:'DeepSeek',model:'deepseek-v4-pro',has_key:true}]}),
  research_request:async p=>{
    if(p.operation==='list')return {ok:true,tasks:task?[task]:[]};
    if(p.operation==='create')task={taskId:'research-preview',version:1,state:'DRAFT',prompt:p.prompt,draft:null};
    if(p.operation==='draft'){task.version++;task.draft={objective:'求解一维 Poisson 问题，并检查参考误差。',equation:"-u''(x)=pi^2*sin(pi*x)",domain:[0,1],boundary:{left:0,right:0},assumptions:[{source:'USER',text:'端点采用齐次 Dirichlet 边界条件。',quote:'u(0)=u(1)=0'}],missing:[],conflicts:[],supported:true,supportMessage:'问题已整理。请核对模型与假设。',template:{reference:'sin(pi*x)',solver:'PINN hard BC x(1-x)N',method:{"configId": "leo-poisson1d-hard-bc-v1", "network": "3 层 × 32 神经元，tanh 激活；输出 u = x(1−x)·N(x)，两端边界值精确为 0（硬边界）", "training": "Adam，学习率 1e-3 指数衰减至 1e-5，固定 6000 步，批量 128，不提前停止", "sampling": "1024 点候选池（种子 20260915）中每个种子无放回抽取 256 个配点", "losses": "PDE 残差权重 1.0，边界权重 10.0", "seeds": "10 个种子，初始化、采样、批次三元组各自登记", "precision": "CPU，float64", "reference": "解析解 u(x) = sin(πx)，另有独立有限差分对照", "acceptance": "相对 L2 误差 ≤ 1e-3（AC-1）；AC-1…AC-8 冻结阈值；最坏种子 ≤ 3 倍 ε；MUST 判据每个种子都须满足", "validation": "主实验 G1–G5 → Tier-1 扰动 → 独立环境复现 → G6", "claimRule": "六个可信维度全部 PASS 才允许 C2；任一未过则只报告被阻断的原因"}}};}
    if(p.operation.startsWith('approve'))return {ok:false,message:'预览不能签署人工确认。'};
    return {ok:true,task,verification:{verified:false,allowedClaims:[],reason:'DRAFT'}};
  },
  open_model_settings:async()=>({ok:false,message:'预览不打开模型设置。'}),copy_text:async()=>({ok:true}),return_to_start:async()=>({ok:false,message:'预览不修改模型设置。'})
}};
})();
