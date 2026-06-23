const CORS = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Methods": "POST, OPTIONS",
  "Access-Control-Allow-Headers": "Content-Type, Authorization",
};

const UA = { "User-Agent": "sathya-reviews-worker/1.0" };

export default {
  async fetch(request, env) {
    if (request.method === "OPTIONS") {
      return new Response(null, { status: 204, headers: CORS });
    }

    if (request.method !== "POST") {
      return new Response("Method not allowed", { status: 405, headers: CORS });
    }

    const auth = request.headers.get("Authorization");
    if (auth !== `Bearer ${env.PUSH_SECRET}`) {
      return new Response("Unauthorized", { status: 401, headers: CORS });
    }

    let path, content, message;
    try {
      ({ path, content, message } = await request.json());
    } catch (e) {
      return new Response("Invalid JSON", { status: 400, headers: CORS });
    }

    if (!path || !content || !message) {
      return new Response("Missing fields", { status: 400, headers: CORS });
    }

    const token = env.GITHUB_TOKEN;
    const repo = "Rocklinks/greviews.tracker";
    const branch = "main";

    // Step 1: Get current file SHA
    const getUrl = `https://api.github.com/repos/${repo}/contents/${path}?ref=${branch}`;
    const getR = await fetch(getUrl, {
      headers: {
        ...UA,
        Authorization: `token ${token}`,
        Accept: "application/vnd.github.v3+json",
      },
    });

    let sha = null;
    if (getR.ok) {
      const gd = await getR.json();
      sha = gd.sha;
    }

    // Step 2: PUT update
    const body = { message, content, branch };
    if (sha) body.sha = sha;

    const putR = await fetch(
      `https://api.github.com/repos/${repo}/contents/${path}`,
      {
        method: "PUT",
        headers: {
          ...UA,
          Authorization: `token ${token}`,
          "Content-Type": "application/json",
          Accept: "application/vnd.github.v3+json",
        },
        body: JSON.stringify(body),
      }
    );

    if (!putR.ok) {
      let errMsg = "Push failed";
      try {
        const err = await putR.json();
        errMsg = err.message || JSON.stringify(err);
      } catch (e) {
        errMsg = `HTTP ${putR.status}`;
      }
      return new Response(JSON.stringify({ error: errMsg }), {
        status: putR.status,
        headers: { ...CORS, "Content-Type": "application/json" },
      });
    }

    return new Response(JSON.stringify({ ok: true }), {
      status: 200,
      headers: { ...CORS, "Content-Type": "application/json" },
    });
  },
};
