from flask import Flask, redirect, url_for, session, request, render_template
from oauthlib.oauth2 import WebApplicationClient
import requests
import json
import os

app = Flask(__name__)
app.secret_key = os.urandom(24)

with open('../config/config.json') as f:
    config = json.load(f)

client = WebApplicationClient(config["discord_client_id"])

DISCORD_AUTH_BASE_URL = "https://discord.com/api/oauth2/authorize"
DISCORD_TOKEN_URL = "https://discord.com/api/oauth2/token"
DISCORD_API_BASE_URL = "https://discord.com/api"

def get_discord_login_url():
    return client.prepare_request_uri(
        DISCORD_AUTH_BASE_URL,
        redirect_uri=config["discord_redirect_uri"],
        scope=["identify", "guilds", "guilds.members.read"]
    )

@app.route("/")
def index():
    if 'user_id' in session:
        return render_template("index.html", user=session['user_id'])
    else:
        return redirect(url_for("login"))

@app.route("/login")
def login():
    discord_login_url = get_discord_login_url()
    return redirect(discord_login_url)

@app.route("/callback")
def callback():
    # Discord로부터 토큰 교환
    code = request.args.get("code")
    token_url, headers, body = client.prepare_token_request(
        DISCORD_TOKEN_URL,
        authorization_response=request.url,
        redirect_url=config["discord_redirect_uri"],
        code=code
    )
    token_response = requests.post(
        token_url,
        headers=headers,
        data=body,
        auth=(config["discord_client_id"], config["discord_client_secret"])
    )
    client.parse_request_body_response(json.dumps(token_response.json()))

    # 사용자 정보 가져오기
    uri, headers, body = client.add_token(f"{DISCORD_API_BASE_URL}/users/@me")
    user_info = requests.get(uri, headers=headers, data=body).json()
    session['user_id'] = user_info['id']

    # 사용자의 길드 및 역할 가져오기
    guild_id = config["guild_id"]
    uri, headers, body = client.add_token(f"{DISCORD_API_BASE_URL}/users/@me/guilds/{guild_id}/member")
    guild_info = requests.get(uri, headers=headers, data=body).json()

    # 역할 확인
    if int(config["admin_role_id"]) in [role["id"] for role in guild_info["roles"]]:
        return redirect(url_for("index"))
    else:
        return "권한이 없습니다. 관리자에게 문의하세요.", 403

if __name__ == "__main__":
    app.run(debug=True)
