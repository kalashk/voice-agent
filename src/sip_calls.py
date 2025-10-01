import os
import uuid
import asyncio
from dotenv import load_dotenv
from livekit import api
from livekit.api import StopEgressRequest, GCPUpload
from livekit.protocol.sip import (
    CreateSIPOutboundTrunkRequest,
    SIPOutboundTrunkInfo,
    CreateSIPParticipantRequest,
    ListSIPOutboundTrunkRequest,
)
from livekit.api import EncodedFileOutput, RoomCompositeEgressRequest
from livekit.protocol.room import ListParticipantsRequest


# --------------------------
# Load environment variables
# --------------------------
load_dotenv(".env.local")

LIVEKIT_API_KEY = os.environ["LIVEKIT_API_KEY"]
LIVEKIT_API_SECRET = os.environ["LIVEKIT_API_SECRET"]
LIVEKIT_URL = os.environ["LIVEKIT_URL"]
GCP_BUCKET = os.environ["GCP_BUCKET"]

TRUNK_NAME = os.environ.get("TRUNK_NAME", "My outbound trunk")
TRUNK_ADDRESS = os.environ.get("TRUNK_ADDRESS", "livekit-sip-outbound-trunk.pstn.twilio.com")
TRUNK_NUMBER = os.environ.get("TRUNK_NUMBER", "+17473503389")
TRUNK_USERNAME = os.environ["TRUNK_USERNAME"]
TRUNK_PASSWORD = os.environ["TRUNK_PASSWORD"]
CALL_TO_NUMBER = os.environ["CALL_TO_NUMBER"]

# participant_identity = f"sip-{uuid.uuid4().hex[:4]}"

# --------------------------
# Create or Get SIP Trunk
# --------------------------
async def create_or_get_trunk():
    """Get existing SIP trunk or create a new one if not found."""
    async with api.LiveKitAPI(LIVEKIT_URL, LIVEKIT_API_KEY, LIVEKIT_API_SECRET) as lkapi:
        request = ListSIPOutboundTrunkRequest()
        trunks_response = await lkapi.sip.list_sip_outbound_trunk(request)

        for t in getattr(trunks_response, "trunks", []):
            if t.name == TRUNK_NAME:
                print(f"✅ Using existing trunk: {t.sip_trunk_id}")
                return t.sip_trunk_id

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
# Make SIP Call
# --------------------------
async def make_call(phone_number: str, sip_trunk_id: str, room_name: str, participant_identity: str):
    """Dial the phone number via SIP trunk and join to LiveKit room."""
    async with api.LiveKitAPI(LIVEKIT_URL, LIVEKIT_API_KEY, LIVEKIT_API_SECRET) as lkapi:
        request = CreateSIPParticipantRequest(
            sip_trunk_id=sip_trunk_id,
            sip_number=TRUNK_NUMBER,
            sip_call_to=phone_number,
            room_name=room_name,
            participant_identity=participant_identity,
            participant_name=f"Customer {phone_number}",
            wait_until_answered=True,
        )

        try:
            participant = await lkapi.sip.create_sip_participant(request)
            if participant:
                print(f"📞 Call to {phone_number} connected in room {room_name}")
                return participant
            print(f"❌ Call to {phone_number} not answered")
            return None
        except Exception as e:
            print(f"❌ Failed to call {phone_number}: {e}")
            return None

# --------------------------
# Start Audio Recording
# --------------------------
async def start_audio_recording(room_name: str):
    async with api.LiveKitAPI(LIVEKIT_URL, LIVEKIT_API_KEY, LIVEKIT_API_SECRET) as lkapi:
        # Keyless GCP upload using VM-attached service account
        file_output = EncodedFileOutput(
            gcp=GCPUpload(bucket=GCP_BUCKET)
        )
        print(f"☁️ Recording will be saved to GCP bucket: {GCP_BUCKET}")

        egress_req = RoomCompositeEgressRequest(
            room_name=room_name,
            audio_only=True,
            file_outputs=[file_output],
        )

        egress_info = await lkapi.egress.start_room_composite_egress(egress_req)
        print(f"🎙️ Recording started for room {room_name}, egress ID: {egress_info.egress_id}")
        return egress_info

# --------------------------
# Stop Audio Recording
# --------------------------
async def stop_audio_recording(egress_id: str):
    """Stop an active egress recording."""
    async with api.LiveKitAPI(LIVEKIT_URL, LIVEKIT_API_KEY, LIVEKIT_API_SECRET) as lkapi:
        try:
            await lkapi.egress.stop_egress(StopEgressRequest(egress_id=egress_id))
            print(f"🛑 Recording stopped for egress {egress_id}")
        except Exception as e:
            print(f"❌ Failed to stop recording {egress_id}: {e}")

# --------------------------
# Run Calls
# --------------------------
async def run_calls_very_simple():
    """
    1. Create a trunk id
    2. make a call to the participant's number
    3. start audio recording after participant joins
    4. stop the recording after participant left
    """
    # Ensure trunk exists
    trunk_id = await create_or_get_trunk()
    print(f"🔑 Final trunk ID to use: {trunk_id}")

    # Make calls
    numbers = [CALL_TO_NUMBER]  # extend this list if needed
    for number in numbers:
        participant_identity = f"sip-{uuid.uuid4().hex[:4]}"
        room_name = f"room-{uuid.uuid4().hex[:4]}"
        participant = await make_call(number, trunk_id, room_name=room_name, participant_identity=participant_identity)
        if participant:
            # Start recording
            egress_info = await start_audio_recording(participant.room_name)
            async with api.LiveKitAPI(LIVEKIT_URL, LIVEKIT_API_KEY, LIVEKIT_API_SECRET) as lkapi:
                while True:
                    participants_resp = await lkapi.room.list_participants(
                        ListParticipantsRequest(room=room_name)
                    )
                    identities = [p.identity for p in participants_resp.participants]
                    if participant_identity not in identities:
                        print("📴 Participant left, stopping recording.")
                        await stop_audio_recording(egress_info.egress_id)
                        break
                    await asyncio.sleep(5)

# --------------------------
# Main       
# --------------------------
if __name__ == "__main__":
    asyncio.run(run_calls_very_simple())
