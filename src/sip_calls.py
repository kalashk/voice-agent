import os
import uuid
import asyncio
from pathlib import Path
from dotenv import load_dotenv
from livekit import api
from livekit.api import ListEgressRequest, StopEgressRequest
from livekit.protocol.sip import (
    CreateSIPOutboundTrunkRequest,
    SIPOutboundTrunkInfo,
    CreateSIPParticipantRequest,
    ListSIPOutboundTrunkRequest
)
from livekit.api import (
    EncodedFileOutput,
    RoomCompositeEgressRequest,
    GCPUpload,
    ListEgressResponse
)
from livekit.protocol.egress import (
    RoomCompositeEgressRequest,
    StopEgressRequest,   # 👈 add this
    ListEgressResponse,
)
from livekit.protocol.room import ListParticipantsRequest


# --------------------------
# Load environment variables
# --------------------------
load_dotenv(".env.local")  # loads .env.local

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

participant_identity = f"sip-{uuid.uuid4().hex[:4]}"

# --------------------------
# Create or Get SIP Trunk
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
# Make SIP Call
# --------------------------
async def make_call(phone_number: str, sip_trunk_id: str, participant_identity: str):
    room_name = f"room-{uuid.uuid4().hex[:4]}"

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
            print(f"📞 Call to {phone_number} connected (participant {participant_identity}) in room {room_name}")
            return participant
        except Exception as e:
            print(f"❌ Failed to call {phone_number}: {e}")

# --------------------------
# Start Audio Recording
# --------------------------
async def start_audio_recording(room_name: str, participant_identity: str):
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

        try:
            egress_info = await lkapi.egress.start_room_composite_egress(egress_req)
            print(f"🎙️ Egress request sent, ID: {egress_info.egress_id}")
        except Exception as e:
            print(f"❌ Failed to start recording for room {room_name}: {e}")
            return None

        # --------------------------
        # Immediate status check
        try:
            response = await lkapi.egress.list_egress(ListEgressRequest(room_name=room_name))
            if response.items:
                e = response.items[0]
                if e.status == 0:
                    print(f"▶️ Recording is now active for room {room_name}")
                elif e.status == 1:
                    print(f"⏳ Recording is starting for room {room_name}")
                elif e.status == 2:
                    print(f"✅ Recording already completed for room {room_name}")
        except Exception as e:
            print(f"❌ Failed to check initial recording status: {e}")

        print(f"⏳ Waiting for recording to complete...")

        # --------------------------
        # Poll until completed or participant disconnects
        while True:
            try:
                # Check egress status
                response: ListEgressResponse = await lkapi.egress.list_egress(
                    ListEgressRequest(room_name=room_name)
                )
                egress = response.items[0] if response.items else None

                # Check participant presence
                resp = await lkapi.room.list_participants(ListParticipantsRequest(room=room_name))
                participants = resp.participants
                participant_connected = any(p.identity == participant_identity for p in participants)

                if egress:
                    if egress.status == 0:
                        print(f"▶️ Recording in progress...")
                    elif egress.status == 2:  # completed
                        if egress.file and hasattr(egress.file, "location"):
                            print(f"✅ Recording completed. File location: {egress.file.location}")
                        else:
                            print("✅ Recording completed, but file location not available")
                        break
                    elif egress.status == 3:  # failed
                        print(f"❌ Recording failed for room {room_name}")
                        break

                # Stop recording if participant disconnected
                if not participant_connected and egress and egress.status == 0:
                    await lkapi.egress.stop_egress(StopEgressRequest(egress_id=egress.egress_id))
                    print(f"🛑 Participant disconnected, stopping recording for room {room_name}")
                    break

                await asyncio.sleep(5)

            except Exception as e:
                print(f"❌ Failed during recording polling: {e}")
                await asyncio.sleep(5)

        return egress_info



# --------------------------
# Run Calls
# --------------------------
async def run_calls():
    # Ensure trunk exists
    trunk_id = await create_or_get_trunk()
    print(f"🔑 Final trunk ID to use: {trunk_id}")

    # Make calls
    numbers = [CALL_TO_NUMBER]  # extend this list if needed
    for number in numbers:
        participant = await make_call(number, trunk_id, participant_identity)
        if participant:
            # Start recording
            await start_audio_recording(participant.room_name, participant_identity)

# --------------------------
# Main
# --------------------------
if __name__ == "__main__":
    asyncio.run(run_calls())
