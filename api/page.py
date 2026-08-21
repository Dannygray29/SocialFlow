from pathlib import Path
from fastapi import FastAPI
from fastapi.responses import HTMLResponse

app = FastAPI()

@app.get("/", response_class=HTMLResponse)
async def page():
    html = Path("frontend/index.html").read_text(encoding="utf-8")
    html = html.replace("const API = 'http://localhost:8000/api';", "const API = '/api';")

    # OAuth-first account buttons. Facebook and YouTube never ask for passwords.
    old_button = "<button className={`btn btn-${p.id}`} onClick={() => setModal(p.id)}>\n                                                + Add Account\n                                            </button>"
    new_button = "<button className={`btn btn-${p.id}`} onClick={() => ['twitter','facebook','youtube'].includes(p.id) ? window.location.assign(`/api/${p.id}_connect`) : setModal(p.id)}>\n                                                {['twitter','facebook','youtube'].includes(p.id) ? (p.id === 'twitter' ? '𝕏 Connect X' : p.id === 'facebook' ? '📘 Connect Facebook' : '▶️ Connect YouTube') : '+ Add Account'}\n                                            </button>"
    html = html.replace(old_button, new_button, 1)

    # Add the two new platforms to the account list.
    html = html.replace(
        "const platforms = [\n                { id: 'linkedin', name: 'LinkedIn', desc: 'Professional network' },\n                { id: 'instagram', name: 'Instagram', desc: 'Photo & video sharing' },\n                { id: 'twitter', name: 'X (Twitter)', desc: 'Real-time updates' }\n            ];",
        "const platforms = [\n                { id: 'linkedin', name: 'LinkedIn', desc: 'Professional network' },\n                { id: 'instagram', name: 'Instagram', desc: 'Photo & video sharing' },\n                { id: 'twitter', name: 'X (Twitter)', desc: 'Real-time updates' },\n                { id: 'facebook', name: 'Facebook Page', desc: 'Page publishing via Meta OAuth' },\n                { id: 'youtube', name: 'YouTube', desc: 'Channel publishing via Google OAuth' }\n            ];",
        1,
    )

    # Replace the credential warning with OAuth explanation.
    html = html.replace(
        "Add your credentials to enable automated posting. All passwords are encrypted locally.",
        "Connect accounts with official OAuth. SocialFlow never asks for your Facebook or YouTube password.",
        1,
    )
    html = html.replace(
        "<p><strong>1. Add your credentials</strong> - Your password is encrypted and stored locally</p>\n                            <p><strong>2. Click Login</strong> - A browser window opens for you to complete login</p>\n                            <p><strong>3. Handle any verification</strong> - Complete 2FA or security checks if prompted</p>\n                            <p><strong>4. You're connected!</strong> - The session is saved for automated posting</p>",
        "<p><strong>1. Connect with OAuth</strong> - SocialFlow sends you to Facebook, Google, or X</p>\n                            <p><strong>2. Approve access</strong> - Grant only the permissions required for publishing</p>\n                            <p><strong>3. Return to SocialFlow</strong> - Your connection is encrypted in an HttpOnly cookie</p>\n                            <p><strong>4. Automation runs</strong> - Content can be scheduled and published without sharing your password</p>",
        1,
    )

    # Add Facebook/YouTube status to the initial app load and keep X status working.
    old_load = """const [postsRes, accountsRes, xRes] = await Promise.all([\n                        api.get('/posts'),\n                        api.get('/accounts'),\n                        api.get('/x/status')\n                    ]);\n                    setPosts(postsRes.posts || []);\n                    const baseAccounts = accountsRes.accounts || [];\n                    const withoutX = baseAccounts.filter(a => a.platform !== 'twitter');\n                    const merged = xRes.connected ? [...withoutX, { platform: 'twitter', username: '@' + xRes.username, is_logged_in: 1 }] : baseAccounts;\n                    setAccounts(merged);"""
    new_load = """const [postsRes, accountsRes, xRes, facebookRes, youtubeRes] = await Promise.all([\n                        api.get('/posts'),\n                        api.get('/accounts'),\n                        api.get('/x/status'),\n                        api.get('/facebook_status'),\n                        api.get('/youtube_status')\n                    ]);\n                    setPosts(postsRes.posts || []);\n                    let merged = (accountsRes.accounts || []).filter(a => !['twitter','facebook','youtube'].includes(a.platform));\n                    if (xRes.connected) merged.push({ platform: 'twitter', username: '@' + xRes.username, is_logged_in: 1 });\n                    if (facebookRes.connected) merged.push({ platform: 'facebook', username: facebookRes.page_name, is_logged_in: 1 });\n                    if (youtubeRes.connected) merged.push({ platform: 'youtube', username: youtubeRes.channel_name, is_logged_in: 1 });\n                    setAccounts(merged);"""
    html = html.replace(old_load, new_load, 1)

    # Content generator can target Facebook and YouTube as well.
    html = html.replace("['linkedin', 'instagram', 'twitter']", "['linkedin', 'instagram', 'twitter', 'facebook', 'youtube']")

    # Route publish requests for Facebook through its Graph API publisher.
    old_publish = """if (publish && post.id) {\n                    await api.post(`/posts/${post.id}/publish`);\n                }"""
    new_publish = """if (publish && post.id) {\n                    if (platform === 'facebook') {\n                        await api.post('/facebook_publish', { message: generated });\n                    } else {\n                        await api.post(`/posts/${post.id}/publish`);\n                    }\n                }"""
    html = html.replace(old_publish, new_publish, 1)

    # Update the connected-count label used by the dashboard.
    html = html.replace("{accounts.filter(a => a.is_logged_in).length}/3", "{accounts.filter(a => a.is_logged_in).length}/5")

    return HTMLResponse(html, headers={"Cache-Control": "no-store"})
