import os
import uuid
import asyncio
from livekit import api
from livekit.protocol.sip import (
    CreateSIPOutboundTrunkRequest,
    SIPOutboundTrunkInfo,
    CreateSIPParticipantRequest,
    ListSIPOutboundTrunkRequest
)
from livekit.api import EncodedFileOutput, RoomCompositeEgressRequest,EncodingOptionsPreset, GCPUpload
from dotenv import load_dotenv
from config import REC_PATH

# --------------------------
# Load environment variables
# --------------------------
load_dotenv(".env.local")  # loads .env.local

LIVEKIT_API_KEY = os.environ["LIVEKIT_API_KEY"]
LIVEKIT_API_SECRET = os.environ["LIVEKIT_API_SECRET"]
LIVEKIT_URL = os.environ["LIVEKIT_URL"]

TRUNK_NAME = os.environ.get("TRUNK_NAME", "My outbound trunk")
TRUNK_ADDRESS = os.environ.get("TRUNK_ADDRESS", "livekit-sip-outbound-trunk.pstn.twilio.com")
TRUNK_NUMBER = os.environ.get("TRUNK_NUMBER", "+17473503389")
TRUNK_USERNAME = os.environ["TRUNK_USERNAME"]
TRUNK_PASSWORD = os.environ["TRUNK_PASSWORD"]
CALL_TO_NUMBER = os.environ["CALL_TO_NUMBER"]
ROOM_NAME = os.environ.get("ROOM_NAME", "open-room")
GCP_CREDENTIALS_PATH = os.environ["GCP_CREDENTIALS_JSON"]
GCP_BUCKET = os.environ["GCP_BUCKET"]

participant_identity = f"sip-{uuid.uuid4().hex[:8]}"

# --------------------------
#   Create or Get SIP Trunk
# --------------------------
async def create_or_get_trunk():
    async with api.LiveKitAPI(LIVEKIT_URL, LIVEKIT_API_KEY, LIVEKIT_API_SECRET) as lkapi:
        request = ListSIPOutboundTrunkRequest()
        trunks_response = await lkapi.sip.list_sip_outbound_trunk(request)

        for t in getattr(trunks_response, "trunks", []):
            if t.name == TRUNK_NAME:
                print(f"✅ Using existing trunk: {t.sip_trunk_id}")
                return t.sip_trunk_id

        # If not found, create one
        trunk = SIPOutboundTrunkInfo(
            name=TRUNK_NAME,
            address=TRUNK_ADDRESS,
            numbers=[TRUNK_NUMBER],
            auth_username=TRUNK_USERNAME,
            auth_password=TRUNK_PASSWORD,
        )
        create_request = CreateSIPOutboundTrunkRequest(trunk=trunk)
        created_trunk = await lkapi.sip.create_sip_outbound_trunk(create_request)

        print(f"✅ Created new trunk: {created_trunk.sip_trunk_id}")
        return created_trunk.sip_trunk_id


# --------------------------
#   Make SIP Call
# --------------------------
async def make_call(phone_number: str, sip_trunk_id: str, participant_identity: str):
    room_name = f"room-{uuid.uuid4().hex[:6]}"

    async with api.LiveKitAPI(LIVEKIT_URL, LIVEKIT_API_KEY, LIVEKIT_API_SECRET) as lkapi:
        request = CreateSIPParticipantRequest(
            sip_trunk_id=sip_trunk_id,
            sip_number=TRUNK_NUMBER,
            sip_call_to=phone_number,
            room_name=room_name,  # new unique room
            participant_identity=participant_identity,
            participant_name=f"Customer {phone_number}",
            wait_until_answered=True,
        )

        try:
            participant = await lkapi.sip.create_sip_participant(request)
            print(f"📞 Call to {phone_number} connected (participant {participant_identity}) in room {room_name}")
            return participant
        except Exception as e:
            print(f"❌ Failed to call {phone_number}: {e}")

# --------------------
# Audio Recorder
# --------------------
async def start_audio_recording(room_name: str, participant_identity: str, use_local=True):
    async with api.LiveKitAPI(LIVEKIT_URL, LIVEKIT_API_KEY, LIVEKIT_API_SECRET) as lkapi:

        if use_local:
            # Save locally
            file_output = EncodedFileOutput(
                filepath=str(REC_PATH / f"{room_name}-{participant_identity}.mp4")
            )
            print("📁 Recording will be saved locally")
        else:
            # Save to GCP
            with open(GCP_CREDENTIALS_PATH, "r") as f:
                gcp_credentials = f.read()
            file_output = EncodedFileOutput(
                filepath=f"/recordings/{room_name}-{participant_identity}.mp4",
                gcp=GCPUpload(
                    credentials=gcp_credentials,
                    bucket=GCP_BUCKET
                )
            )
            print(f"☁️ Recording will be saved to GCP bucket: {GCP_BUCKET}")

        # file_outputs must be a list
        egress_req = RoomCompositeEgressRequest(
            room_name=room_name,
            layout="speaker",
            audio_only=True,
            preset=EncodingOptionsPreset.H264_720P_30,
            file_outputs=[file_output],
        )

        egress_info = await lkapi.egress.start_room_composite_egress(egress_req)
        print(f"🎙️ Recording started for room {room_name}, egress ID: {egress_info.egress_id}")
        return egress_info

# --------------------------  
#   Run Multiple Calls  
# --------------------------  
async def run_calls():
    # Step 1: Ensure trunk exists
    trunk_id = await create_or_get_trunk()
    print(f"🔑 Final trunk ID to use: {trunk_id}")

    # Step 2: Make calls using that trunk
    numbers = [CALL_TO_NUMBER]  # could be extended
    for number in numbers:
        participant = await make_call(number, trunk_id, participant_identity)
        if participant:
            # Start recording for this participant
            await start_audio_recording(participant.room_name, participant_identity, use_local=True)



if __name__ == "__main__":
    asyncio.run(run_calls())
