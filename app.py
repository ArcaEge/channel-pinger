import logging

logging.basicConfig(level=logging.DEBUG)
logging.getLogger("sqlalchemy.engine").setLevel(logging.INFO)

import os
from slack_bolt import App
from slack_bolt.adapter.flask import SlackRequestHandler
from slack_bolt.oauth.oauth_settings import OAuthSettings
from slack_sdk.oauth.installation_store.sqlalchemy import SQLAlchemyInstallationStore
from slack_sdk.oauth.state_store.sqlalchemy import SQLAlchemyOAuthStateStore
from dotenv import load_dotenv

load_dotenv()

import sqlalchemy
from sqlalchemy.engine import Engine

database_url = "sqlite:///database.db"
# database_url = "postgresql://localhost/slackapp"  # pip install psycopg2

logger = logging.getLogger(__name__)
client_id, client_secret, signing_secret, host = (
    os.environ["SLACK_CLIENT_ID"],
    os.environ["SLACK_CLIENT_SECRET"],
    os.environ["SLACK_SIGNING_SECRET"],
    os.environ["APP_HOST"],
)

engine: Engine = sqlalchemy.create_engine(database_url)
installation_store = SQLAlchemyInstallationStore(
    client_id=client_id,
    engine=engine,
    logger=logger,
)
oauth_state_store = SQLAlchemyOAuthStateStore(
    expiration_seconds=120,
    engine=engine,
    logger=logger,
)

try:
    engine.execute("select count(*) from slack_bots")
except Exception as e:
    installation_store.metadata.create_all(engine)
    oauth_state_store.metadata.create_all(engine)

app = App(
    logger=logger,
    signing_secret=signing_secret,
    installation_store=installation_store,
    oauth_settings=OAuthSettings(
        redirect_uri=f"https://{host}/slack/oauth_redirect",
        client_id=client_id,
        client_secret=client_secret,
        state_store=oauth_state_store,
        user_scopes=["chat:write"],
    ),
)


@app.event("app_mention")
def handle_command(say):
    say("@channel")

@app.command("/channel-as-me")
def handle_channel_command(ack, body, respond, say):
    ack()
    respond("[insert channel ping]")
    say({
	"blocks": [
		{
			"type": "section",
			"block_id": "aPtBq",
			"text": {
				"type": "mrkdwn",
				"text": "@channel test ping but this will be sent through the user later",
				"verbatim": False
			}
		}
	]
})


from flask import Flask, request

flask_app = Flask(__name__)
handler = SlackRequestHandler(app)


@flask_app.route("/slack/events", methods=["POST"])
def slack_events():
    return handler.handle(request)

@flask_app.route("/slack/install", methods=["GET"])
def install():
    return handler.handle(request)


@flask_app.route("/slack/oauth_redirect", methods=["GET"])
def oauth_redirect():
    return handler.handle(request)

if __name__ == "__main__":
    app.start(3000)