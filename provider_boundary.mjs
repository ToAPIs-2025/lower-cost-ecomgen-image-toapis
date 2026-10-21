/** Optional Node backend boundary. Never import this module into browser code. */
import {spawn} from 'node:child_process';
import {readFile} from 'node:fs/promises';
import {fileURLToPath} from 'node:url';

export function generateAsset(input) {
  return new Promise((resolve,reject)=>{
    const child=spawn(process.env.TOAPIS_PYTHON || 'python',[fileURLToPath(new URL('./provider_entry.py',import.meta.url))],{env:process.env,windowsHide:true,stdio:['pipe','pipe','pipe']});
    let output='';child.stdout.on('data',b=>output+=b);child.stderr.on('data',()=>{});
    child.on('error',reject);child.on('close',code=>{
      try {const result=JSON.parse(output);if(code!==0 || result.error)throw new Error(result.message || 'Provider failed');resolve(result);}catch(e){reject(e);}
    });child.stdin.end(JSON.stringify(input));
  });
}

/** Matches Loomic's ImageProvider result, with an explicit supported subset. */
export class ToApisImageProvider {
  name='toapis';
  models=[{id:'toapis/gpt-image-2',displayName:'gpt-image-2 · ToAPIs',description:'Optional text-to-image; 1K PNG.'},{id:'toapis/gpt-image-2-vip',displayName:'gpt-image-2(VIP) · ToAPIs',description:'Optional text-to-image; low / 1K PNG.'}];
  async generate(params) {
    if(!this.models.some(m=>m.id===params.model) || params.inputImages?.length || ![undefined,'standard'].includes(params.quality) || ![undefined,'1:1'].includes(params.aspectRatio) || ![undefined,'png'].includes(params.outputFormat))throw new Error('Only reviewed square 1K text-to-image PNG presets are mapped; edits and other presets are not enabled');
    const result=await generateAsset({model:params.model.slice('toapis/'.length),prompt:params.prompt,jobId:params.metadata?.toapisJobId});
    const raw=await readFile(result.file);return {url:`data:${result.mimeType};base64,${raw.toString('base64')}`,mimeType:result.mimeType,width:result.width,height:result.height};
  }
}

/** Matches EcomGen's ImageGenerationResult; editing is deliberately separate. */
export async function generateEcomImage(input) {
  if(input.images?.length || input.mask || input.operation || input.background==='transparent' || ![undefined,'1024x1024'].includes(input.size) || ![undefined,'high'].includes(input.quality) || ![undefined,'png'].includes(input.outputFormat))throw new Error('This contribution maps text-to-image high/1K only; no edit, mask or transparency capability is asserted');
  if(input.model!=='gpt-image-2.5-flare')throw new Error('Model not enabled for this integration');
  if(input.signal?.aborted)throw new Error('Cancelled before submission');
  const result=await generateAsset({model:input.model,prompt:input.prompt,jobId:input.idempotencyKey});
  // Aborting a local caller does not promise remote cancellation/refund.
  if(input.signal?.aborted)throw new Error('Caller cancelled; resume the stored task, do not resubmit');
  return {image:await readFile(result.file),mimeType:result.mimeType};
}
