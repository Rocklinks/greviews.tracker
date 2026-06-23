export default {
  async fetch(request, env) {
    if (request.method !== "POST") {
      return new Response("Method not allowed", { status: 405 });
    }

    const auth = request.headers.get("Authorization");
    if (auth !== `Bearer ${env.PUSH_SECRET}`) {
      return new Response("Unauthorized", { status: 401 });
    }

    const { path, content, message } = await request.json();
    if (!path || !content || !message) {
      return new Response("Missing fields", { status: 400 });
    }

    const token = env.GITHUB_TOKEN;
    const repo = "Rocklinks/greviews.tracker";
    const branch = "main";

    const getUrl = `https://api.github.com/repos/${repo}/contents/${path}?ref=${branch}`;
    const getR = await fetch(getUrl, {
      headers: {
        Authorization: `token ${token}`,
        Accept: "application/vnd.github.v3+json",
      },
    });

    let sha = null;
    if (getR.ok) {
      const gd = await getR.json();
      sha = gd.sha;
    }

    const body = { message, content, branch };
    if (sha) body.sha = sha;

    const putR = await fetch(
      `https://api.github.com/repos/${repo}/contents/${path}`,
      {
        method: "PUT",
        headers: {
          Authorization: `token ${token}`,
          "Content-Type": "application/json",
          Accept: "application/vnd.github.v3+json",
        },
        body: JSON.stringify(body),
      }
    );

    if (!putR.ok) {
      const err = await putR.json();
      return new Response(JSON.stringify(err), { status: putR.status });
    }

    return new Response(JSON.stringify({ ok: true }), { status: 200 });
  },
};
