from pathlib import Path
from fastapi.responses import HTMLResponse


def handler(request):
    html = Path("frontend/index.html").read_text(encoding="utf-8")
    html = html.replace("const API = 'http://localhost:8000/api';", "const API = '/api';")
    old = "<button className={`btn btn-${p.id}`} onClick={() => setModal(p.id)}>\n                                                + Add Account\n                                            </button>"
    new = "<button className={`btn btn-${p.id}`} onClick={() => p.id === 'twitter' ? window.location.assign('/api/x/connect') : setModal(p.id)}>\n                                                {p.id === 'twitter' ? '𝕏 Connect X' : '+ Add Account'}\n                                            </button>"
    html = html.replace(old, new, 1)
    old_load = """const [postsRes, accountsRes] = await Promise.all([\n                        api.get('/posts'),\n                        api.get('/accounts')\n                    ]);\n                    setPosts(postsRes.posts || []);\n                    setAccounts(accountsRes.accounts || []);"""
    new_load = """const [postsRes, accountsRes, xRes] = await Promise.all([\n                        api.get('/posts'),\n                        api.get('/accounts'),\n                        api.get('/x/status')\n                    ]);\n                    setPosts(postsRes.posts || []);\n                    const baseAccounts = accountsRes.accounts || [];\n                    const withoutX = baseAccounts.filter(a => a.platform !== 'twitter');\n                    const merged = xRes.connected ? [...withoutX, { platform: 'twitter', username: '@' + xRes.username, is_logged_in: 1 }] : baseAccounts;\n                    setAccounts(merged);"""
    html = html.replace(old_load, new_load, 1)
    return HTMLResponse(html, headers={"Cache-Control": "no-store"})
