# Project-specific integration plan

Pinned upstream: https://github.com/linbei0/EcomGen/tree/f8e6e7b52c1ff74a614052728ccb24c2b4c5e7b6

Worker 层可选图片适配函数；返回 image Buffer + mimeType。不能直接把异步 ToAPIs 地址填入同步 OpenAI Images Provider。

Optional ImageGenerationResult boundary passed with the real PNG. No edit/mask/transparency support is asserted. Worker registration and full upstream checks are pending.

## API differences

- Bearer generation key to HTTPS `https://toapis.com` only; image `POST /v1/images/generations`, video `POST /v1/videos/generations`.
- An async task `id` is not OpenAI `data[0]`. Persist it before polling `GET /v1/images/generations/:id` or `/v1/videos/generations/:id`; wait for `completed`, then download `result.data[0].url` without forwarding credentials.
- Local first-frame upload uses `POST /v1/uploads/images`; use `image_with_roles` with `role=first_frame` only for a reviewed I2V preset. Reference editing, mask repaint and arbitrary multimodal inputs are not enabled by this example.
- Match model, quality, resolution, image count, duration, mode and audio to the exact same-key pricing rules. `billing.status=settled` and explicit costs confirm a charge; missing billing stays unknown.
- No automatic paid POST retry. Keep state/receipts private; changing a run ID can cost again.

## Remaining acceptance

1. Confirm the maintainer's desired contribution route and image/video owner.
2. Wire only the supported preset to the normal settings/registry/worker. Do not replace existing defaults or referrals.
3. Verify native create, restart/resume, readable failure, cancel semantics, download and final result placement.
4. Run upstream checks for affected modules and a real application task before calling this native integration accepted.

## Information needed from the maintainer

Target version; preferred Provider identity/configuration; native task cancellation and result persistence contract; permitted example/docs location; existing sponsorship/referral conditions.

## Optional module

`generateEcomImage(input)` returns `{image: Buffer, mimeType}`; use a stable `idempotencyKey`. Only Flare high/1K text-to-image is mapped. Wire a dedicated adapter branch in the Provider package, then export/register it through the normal Worker flow; do not add URL/name branching in business code. Mask/edit/transparent background are rejected. Before a native PR run `pnpm test:affected`, `pnpm --filter @ecomgen/providers test`, `pnpm test:e2e:mock` as required upstream. None of those native changes or suites is claimed complete here.
