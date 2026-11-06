import handler from 'vinext/server/fetch-handler';

/** Sites dispatch handles ChatGPT sign-in and injects the authenticated headers. */
export default {
  fetch(request: Request, env: CloudflareEnv, ctx: ExecutionContext): Promise<Response> {
    return handler.fetch(request, env, ctx);
  },
};
