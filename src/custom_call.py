# import os
# import json
# import logging
# import uuid
# import asyncio
# from dotenv import load_dotenv
# from livekit import api
# from livekit.api import StopEgressRequest, GCPUpload
# from livekit.protocol.sip import (
#     CreateSIPOutboundTrunkRequest,
#     SIPOutboundTrunkInfo,
#     CreateSIPParticipantRequest,
#     ListSIPOutboundTrunkRequest,
# )
# from helpers.customer_helper import update_customer_profile, CustomerProfileType, save_customer_profile
# from livekit.api import EncodedFileOutput, RoomCompositeEgressRequest
# from livekit.protocol.room import ListParticipantsRequest


# # --------------------------
# # Load environment variables
# # --------------------------
# load_dotenv(".env.local")

# LIVEKIT_API_KEY = os.environ["LIVEKIT_API_KEY"]
# LIVEKIT_API_SECRET = os.environ["LIVEKIT_API_SECRET"]
# LIVEKIT_URL = os.environ["LIVEKIT_URL"]
# GCP_BUCKET = os.environ["GCP_BUCKET"]

# TRUNK_NAME = os.environ.get("TRUNK_NAME", "My outbound trunk")
# TRUNK_ADDRESS = os.environ.get("TRUNK_ADDRESS", "livekit-sip-outbound-trunk.pstn.twilio.com")
# TRUNK_NUMBER = os.environ.get("TRUNK_NUMBER", "+17473503389")
# TRUNK_USERNAME = os.environ["TRUNK_USERNAME"]
# TRUNK_PASSWORD = os.environ["TRUNK_PASSWORD"]


# # --------------------------
# # Create or Get SIP Trunk
# # --------------------------
# async def create_or_get_trunk():
#     """Get existing SIP trunk or create a new one if not found."""
#     async with api.LiveKitAPI(LIVEKIT_URL, LIVEKIT_API_KEY, LIVEKIT_API_SECRET) as lkapi:
#         request = ListSIPOutboundTrunkRequest()
#         trunks_response = await lkapi.sip.list_sip_outbound_trunk(request)

#         for t in getattr(trunks_response, "trunks", []):
#             if t.name == TRUNK_NAME:
#                 print(f"✅ Using existing trunk: {t.sip_trunk_id}")
#                 return t.sip_trunk_id

#         trunk = SIPOutboundTrunkInfo(
#             name="tata-sip",
#             address="27.107.220.6:5101",
#             numbers=["00919240908350"],
#             auth_username="00919240908350",
#             auth_password="1234",
#         )
#         create_request = CreateSIPOutboundTrunkRequest(trunk=trunk)
#         created_trunk = await lkapi.sip.create_sip_outbound_trunk(create_request)

#         print(f"✅ Created new trunk: {created_trunk.sip_trunk_id}")
#         return created_trunk.sip_trunk_id


# # --------------------------
# # Make SIP Call
# # --------------------------
# async def make_call(phone_number: str, name: str, gender: str, sip_trunk_id: str, room_name: str, participant_identity: str):
#     """Dial the phone number via SIP trunk and join to LiveKit room."""
#     participant_name = f"{name} ({gender.upper()})"

#     async with api.LiveKitAPI(LIVEKIT_URL, LIVEKIT_API_KEY, LIVEKIT_API_SECRET) as lkapi:
#         request = CreateSIPParticipantRequest(
#             sip_trunk_id=sip_trunk_id,
#             sip_number="00919240908350",
#             sip_call_to=phone_number,
#             room_name=room_name,
#             participant_identity=participant_identity,
#             participant_name=participant_name,
#             wait_until_answered=True,
#         )
#         print(f"📤 SIP request created for {participant_name}...")

#         try:
#             participant = await lkapi.sip.create_sip_participant(request)
#             if participant:
#                 print(f"📞 Call to {participant_name} ({phone_number}) connected in room {room_name}")
#                 return participant
#             print(f"❌ Call to {participant_name} not answered")
#             return None
#         except Exception as e:
#             print(f"❌ Failed to call {participant_name}: {e}")
#             return None


# # --------------------------
# # Start Audio Recording
# # --------------------------
# async def start_audio_recording(room_name: str):
#     async with api.LiveKitAPI(LIVEKIT_URL, LIVEKIT_API_KEY, LIVEKIT_API_SECRET) as lkapi:
#         file_output = EncodedFileOutput(
#             gcp=GCPUpload(bucket=GCP_BUCKET)
#         )
#         print(f"☁️ Recording will be saved to GCP bucket: {GCP_BUCKET}")

#         egress_req = RoomCompositeEgressRequest(
#             room_name=room_name,
#             audio_only=True,
#             file_outputs=[file_output],
#         )

#         egress_info = await lkapi.egress.start_room_composite_egress(egress_req)
#         print(f"🎙️ Recording started for room {room_name}, egress ID: {egress_info.egress_id}")
#         return egress_info


# # --------------------------
# # Stop Audio Recording
# # --------------------------
# async def stop_audio_recording(egress_id: str):
#     """Stop an active egress recording."""
#     async with api.LiveKitAPI(LIVEKIT_URL, LIVEKIT_API_KEY, LIVEKIT_API_SECRET) as lkapi:
#         try:
#             await lkapi.egress.stop_egress(StopEgressRequest(egress_id=egress_id))
#             print(f"🛑 Recording stopped for egress {egress_id}")
#         except Exception as e:
#             print(f"❌ Failed to stop recording {egress_id}: {e}")



# # --------------------------
# # Run Calls
# # --------------------------
# async def run_calls():
#     """
#     1. Create a trunk id
#     2. Ask user for name, gender, and number
#     3. Make call
#     4. Start & stop recording
#     """
#     customer = update_customer_profile()
#     trunk_id = await create_or_get_trunk()

#     print(f"🔑 Using trunk ID: {trunk_id}")

#     participant_identity = f"sip-{uuid.uuid4().hex[:4]}"
#     room_name = f"room-{uuid.uuid4().hex[:4]}"

#     participant = await make_call(
#         phone_number=customer["phone_number"],
#         name=customer["customer_name"],
#         gender=customer["gender"], 
#         sip_trunk_id=trunk_id, 
#         room_name=room_name, 
#         participant_identity=participant_identity
#     )

#     if participant:
#         # Start recording
#         egress_info = await start_audio_recording(participant.room_name)

#         async with api.LiveKitAPI(LIVEKIT_URL, LIVEKIT_API_KEY, LIVEKIT_API_SECRET) as lkapi:
#             while True:
#                 participants_resp = await lkapi.room.list_participants(
#                     ListParticipantsRequest(room=room_name)
#                 )
#                 identities = [p.identity for p in participants_resp.participants]
#                 if participant_identity not in identities:
#                     print("📴 Participant left, stopping recording.")
#                     await stop_audio_recording(egress_info.egress_id)
#                     break


# # --------------------------
# # Run Calls
# # --------------------------
# async def run_calls_rec():
#     """
#     1. Create a trunk id
#     2. Ask user for name, gender, and number
#     3. Make call
#     4. Optionally start & stop recording
#     """
#     customer = update_customer_profile()
    
#     # Ask if recording is needed, default to "N"
#     record_choice = input("🎙️ Do you want to record the call? (Y/N) [N]: ").strip().upper() or "N"
#     do_record = record_choice == "Y"

#     trunk_id = await create_or_get_trunk()
#     print(f"🔑 Using trunk ID: {trunk_id}")

#     participant_identity = f"sip-{uuid.uuid4().hex[:4]}"
#     room_name = f"room-{uuid.uuid4().hex[:4]}"

#     participant = await make_call(
#         phone_number=customer["phone_number"],
#         name=customer["customer_name"],
#         gender=customer["gender"], 
#         sip_trunk_id=trunk_id, 
#         room_name=room_name, 
#         participant_identity=participant_identity
#     )

#     if participant:
#         egress_info = None
#         if do_record:
#             # Start recording if chosen
#             egress_info = await start_audio_recording(participant.room_name)

#         async with api.LiveKitAPI(LIVEKIT_URL, LIVEKIT_API_KEY, LIVEKIT_API_SECRET) as lkapi:
#             while True:
#                 participants_resp = await lkapi.room.list_participants(
#                     ListParticipantsRequest(room=room_name)
#                 )
#                 identities = [p.identity for p in participants_resp.participants]
#                 if participant_identity not in identities:
#                     print("📴 Participant left.")
#                     if do_record and egress_info:
#                         print("🛑 Stopping recording...")
#                         await stop_audio_recording(egress_info.egress_id)
#                     break


# # # --------------------------
# # # Run Multiple Calls
# # # --------------------------
# # async def run_multiple_calls():
# #     """
# #     Make multiple calls concurrently (no recording).
# #     """
# #     num_calls = int(input("📞 How many calls do you want to make? "))

# #     customers = []
# #     for i in range(num_calls):
# #         print(f"\n🧍‍♂️ Customer {i+1}")
# #         name = input("👤 Enter name: ").strip()
# #         gender = input("⚧️ Enter gender (M/F): ").strip().lower()
# #         phone = input("📱 Enter 10-digit phone number: ").strip()
# #         if not phone.startswith("+91"):
# #             phone = "+91" + phone
# #         customers.append({"customer_name": name, "gender": gender, "phone_number": phone})

# #     trunk_id = await create_or_get_trunk()
# #     print(f"\n🔑 Using trunk ID: {trunk_id}")

# #     async def make_individual_call(customer):
# #         room_name = f"room-{uuid.uuid4().hex[:4]}"
# #         participant_identity = f"sip-{uuid.uuid4().hex[:4]}"
# #         try:
# #             participant = await make_call(
# #                 phone_number=customer["phone_number"],
# #                 name=customer["customer_name"],
# #                 gender=customer["gender"],
# #                 sip_trunk_id=trunk_id,
# #                 room_name=room_name,
# #                 participant_identity=participant_identity
# #             )
# #             if participant:
# #                 print(f"✅ Call started for {customer['customer_name']} ({customer['phone_number']})")
# #         except Exception as e:
# #             print(f"❌ Error for {customer['customer_name']}: {e}")

# #     # Launch all calls concurrently
# #     await asyncio.gather(*(make_individual_call(c) for c in customers))

# #     print("\n📞 All calls initiated successfully!")


# # CUSTOMER_FILE = "customer.json"

# # --------------------------
# # Configure Logging
# # --------------------------
# logger = logging.getLogger("multi_call_agent")
# logger.setLevel(logging.INFO)

# handler = logging.StreamHandler()
# formatter = logging.Formatter("[%(asctime)s] [%(levelname)s] %(message)s", "%H:%M:%S")
# handler.setFormatter(formatter)
# logger.addHandler(handler)


# # --------------------------
# # Run Multiple Calls
# # --------------------------
# async def run_multiple_calls():
#     """
#     Make multiple customer calls concurrently.
#     Each call:
#       - Saves its own customer.json before the call (safe)
#       - Makes the call (no recording)
#       - Logs each step
#     """
#     logger.info("🚀 Starting multi-call workflow")

#     num_calls = int(input("📞 How many calls do you want to make? "))
#     customers: list[CustomerProfileType] = []

#     # 🧍 Collect all customer details
#     for i in range(num_calls):
#         print(f"\n🧍‍♂️ Customer {i + 1}")
#         name = input("👤 Enter name: ").strip()
#         gender = input("⚧ Enter gender (M/F): ").strip().upper()
#         gender = "Male" if gender == "M" else "Female" if gender == "F" else gender
#         phone = input("📱 Enter 10-digit phone number: ").strip()
#         if not phone.startswith("+91"):
#             phone = "+91" + phone

#         customer : CustomerProfileType = {
#             "customer_id": f"cust_{uuid.uuid4().hex[:6]}",
#             "customer_name": name,
#             "age": 30,
#             "city": "Pune",
#             "language": "hindi",
#             "bank_name": "HDFC",
#             "phone_number": phone,
#             "gender": gender
#         }

#         logger.info(f"🧾 Added customer {i + 1}: {customer['customer_name']} ({customer['phone_number']})")
#         customers.append(customer)

#     # Create trunk once
#     logger.info("🔄 Creating or fetching trunk ID...")
#     trunk_id = await create_or_get_trunk()
#     logger.info(f"🔑 Using trunk ID: {trunk_id}")

#     async def make_individual_call(customer: CustomerProfileType):
#         """Save profile, then start a single call asynchronously with logging."""
#         cid = customer["customer_id"]
#         prefix = f"[{customer['customer_name']}]"

#         try:
#             # Save the customer profile
#             save_customer_profile(profile=customer)
#             logger.info(f"{prefix} 💾 Profile saved")

#             room_name = f"room-{uuid.uuid4().hex[:4]}"
#             participant_identity = cid

#             logger.info(f"{prefix} 📞 Initiating call to {customer['phone_number']}...")

#             participant = await make_call(
#                 phone_number=customer["phone_number"],
#                 name=customer["customer_name"],
#                 gender=customer["gender"],
#                 sip_trunk_id=trunk_id,
#                 room_name=room_name,
#                 participant_identity=participant_identity
#             )

#             if participant:
#                 logger.info(f"{prefix} ✅ Call successfully started (room: {room_name})")
#             else:
#                 logger.warning(f"{prefix} ⚠️ Call initiation failed or returned None")

#         except Exception as e:
#             logger.error(f"{prefix} ❌ Error during call: {e}", exc_info=True)
#         finally:
#             logger.info(f"{prefix} 📴 Call process ended")

#     # ⚡ Launch all calls concurrently
#     logger.info(f"📲 Launching {num_calls} call(s) concurrently...")
#     await asyncio.gather(*(make_individual_call(c) for c in customers))

#     logger.info("✅ All calls initiated successfully!")



# # --------------------------
# # Main
# # --------------------------
# if __name__ == "__main__":
#     asyncio.run(run_multiple_calls())


import os
import json
import logging
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
from helpers.customer_helper import update_customer_profile, CustomerProfileType, save_customer_profile
from livekit.api import EncodedFileOutput, RoomCompositeEgressRequest
from livekit.protocol.room import ListParticipantsRequest


# --------------------------
# Configure Logging
# --------------------------
logger = logging.getLogger("multi_call_agent")
logger.setLevel(logging.INFO)

handler = logging.StreamHandler()
formatter = logging.Formatter("[%(asctime)s] [%(levelname)s] %(message)s", "%H:%M:%S")
handler.setFormatter(formatter)
logger.addHandler(handler)


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


# --------------------------
# Create or Get SIP Trunk
# --------------------------
async def create_or_get_trunk():
    """Get existing SIP trunk or create a new one if not found."""
    logger.info("🔄 Checking for existing SIP trunk...")
    async with api.LiveKitAPI(LIVEKIT_URL, LIVEKIT_API_KEY, LIVEKIT_API_SECRET) as lkapi:
        try:
            request = ListSIPOutboundTrunkRequest()
            trunks_response = await lkapi.sip.list_sip_outbound_trunk(request)
            for t in getattr(trunks_response, "trunks", []):
                if t.name == TRUNK_NAME:
                    logger.info(f"✅ Using existing trunk: {t.sip_trunk_id}")
                    return t.sip_trunk_id

            logger.info("📞 No existing trunk found, creating a new one...")
            trunk = SIPOutboundTrunkInfo(
                name="tata-sip",
                address="27.107.220.6:5101",
                numbers=["00919240908350"],
                auth_username="00919240908350",
                auth_password="1234",
            )
            create_request = CreateSIPOutboundTrunkRequest(trunk=trunk)
            created_trunk = await lkapi.sip.create_sip_outbound_trunk(create_request)
            logger.info(f"✅ Created new trunk: {created_trunk.sip_trunk_id}")
            return created_trunk.sip_trunk_id
        except Exception as e:
            logger.error(f"❌ Failed to create/get SIP trunk: {e}", exc_info=True)
            raise


# --------------------------
# Make SIP Call
# --------------------------
async def make_call(phone_number: str, name: str, gender: str, sip_trunk_id: str, room_name: str, participant_identity: str):
    """Dial the phone number via SIP trunk and join to LiveKit room."""
    participant_name = f"{name} ({gender.upper()})"
    logger.info(f"📤 Creating SIP request for {participant_name} → {phone_number}")

    async with api.LiveKitAPI(LIVEKIT_URL, LIVEKIT_API_KEY, LIVEKIT_API_SECRET) as lkapi:
        request = CreateSIPParticipantRequest(
            sip_trunk_id=sip_trunk_id,
            sip_number="00919240908350",
            sip_call_to=phone_number,
            room_name=room_name,
            participant_identity=participant_identity,
            participant_name=participant_name,
            wait_until_answered=True,
        )

        try:
            participant = await lkapi.sip.create_sip_participant(request)
            if participant:
                logger.info(f"📞 Call connected: {participant_name} ({phone_number}) in room {room_name}")
                return participant
            logger.warning(f"⚠️ Call to {participant_name} was not answered.")
            return None
        except Exception as e:
            logger.error(f"❌ Failed to make call to {participant_name}: {e}", exc_info=True)
            return None


# --------------------------
# Start Audio Recording
# --------------------------
async def start_audio_recording(room_name: str):
    """Start GCP audio recording."""
    logger.info(f"🎙️ Starting recording for room {room_name}...")
    async with api.LiveKitAPI(LIVEKIT_URL, LIVEKIT_API_KEY, LIVEKIT_API_SECRET) as lkapi:
        try:
            file_output = EncodedFileOutput(gcp=GCPUpload(bucket=GCP_BUCKET))
            egress_req = RoomCompositeEgressRequest(
                room_name=room_name,
                audio_only=True,
                file_outputs=[file_output],
            )
            egress_info = await lkapi.egress.start_room_composite_egress(egress_req)
            logger.info(f"☁️ Recording started for {room_name}, egress ID: {egress_info.egress_id}")
            return egress_info
        except Exception as e:
            logger.error(f"❌ Failed to start recording for {room_name}: {e}", exc_info=True)
            return None


# --------------------------
# Stop Audio Recording
# --------------------------
async def stop_audio_recording(egress_id: str):
    """Stop an active egress recording."""
    logger.info(f"🛑 Stopping recording for egress {egress_id}...")
    async with api.LiveKitAPI(LIVEKIT_URL, LIVEKIT_API_KEY, LIVEKIT_API_SECRET) as lkapi:
        try:
            await lkapi.egress.stop_egress(StopEgressRequest(egress_id=egress_id))
            logger.info(f"✅ Recording stopped successfully (egress: {egress_id})")
        except Exception as e:
            logger.error(f"❌ Failed to stop recording {egress_id}: {e}", exc_info=True)


# --------------------------
# Run Single Call with Optional Recording
# --------------------------
async def run_calls_rec():
    """
    1. Create a trunk id
    2. Ask user for name, gender, and number
    3. Make call
    4. Optionally start & stop recording
    """
    logger.info("🚀 Starting single call workflow with optional recording")

    customer = update_customer_profile()
    record_choice = input("🎙️ Do you want to record the call? (Y/N) [N]: ").strip().upper() or "N"
    do_record = record_choice == "Y"

    trunk_id = await create_or_get_trunk()
    logger.info(f"🔑 Using trunk ID: {trunk_id}")

    participant_identity = f"sip-{uuid.uuid4().hex[:4]}"
    room_name = f"room-{uuid.uuid4().hex[:4]}"

    participant = await make_call(
        phone_number=customer["phone_number"],
        name=customer["customer_name"],
        gender=customer["gender"],
        sip_trunk_id=trunk_id,
        room_name=room_name,
        participant_identity=participant_identity
    )

    if participant:
        egress_info = None
        if do_record:
            egress_info = await start_audio_recording(room_name)

        async with api.LiveKitAPI(LIVEKIT_URL, LIVEKIT_API_KEY, LIVEKIT_API_SECRET) as lkapi:
            logger.info(f"📡 Monitoring participants in room {room_name}...")
            while True:
                participants_resp = await lkapi.room.list_participants(
                    ListParticipantsRequest(room=room_name)
                )
                identities = [p.identity for p in participants_resp.participants]
                if participant_identity not in identities:
                    logger.info("📴 Participant left.")
                    if do_record and egress_info:
                        await stop_audio_recording(egress_info.egress_id)
                    break

# --------------------------
# Run Calls with Rolling Concurrency + Delay
# --------------------------
async def run_parallel_calls(max_concurrent: int = 4, delay_seconds: int = 5):
    """
    Run multiple customer calls concurrently with:
    - Up to `max_concurrent` calls active at any time
    - Delay between starting each call to prevent profile overlap
    - Automatically starts next call as soon as a call finishes
    """

    logger.info(f"🚀 Starting rolling call workflow (max_concurrent={max_concurrent})")

    # 🧍 Hardcoded customer list — edit as needed
    customers: list[CustomerProfileType] = [
        {
            "customer_id": f"cust_{uuid.uuid4().hex[:6]}",
            "customer_name": "Arpit",
            "age": 32,
            "city": "Mumbai",
            "language": "hindi",
            "bank_name": "HDFC",
            "phone_number": "+918127028998",
            "gender": "Male",
        },
        {
            "customer_id": f"cust_{uuid.uuid4().hex[:6]}",
            "customer_name": "Shubham",
            "age": 29,
            "city": "Pune",
            "language": "hindi",
            "bank_name": "HDFC",
            "phone_number": "+919450573909",
            "gender": "Male",
        },
        {
            "customer_id": f"cust_{uuid.uuid4().hex[:6]}",
            "customer_name": "Abhishek",
            "age": 29,
            "city": "Pune",
            "language": "hindi",
            "bank_name": "HDFC",
            "phone_number": "+918953678465",
            "gender": "Male",
        },
        {
            "customer_id": f"cust_{uuid.uuid4().hex[:6]}",
            "customer_name": "Rahul",
            "age": 29,
            "city": "Pune",
            "language": "hindi",
            "bank_name": "HDFC",
            "phone_number": "+919669953995",
            "gender": "Male",
        },
    ]

    logger.info(f"🧾 Loaded {len(customers)} customers for calling")

    # 🔑 Get trunk once
    logger.info("🔄 Creating or fetching trunk ID...")
    trunk_id = await create_or_get_trunk()
    logger.info(f"🔑 Using trunk ID: {trunk_id}")

    # 🎯 Define single call routine
    async def make_individual_call(customer: CustomerProfileType, sem: asyncio.Semaphore):
        async with sem:  # limits concurrency
            prefix = f"[{customer['customer_name']}]"
            try:
                save_customer_profile(profile=customer)
                logger.info(f"{prefix} 💾 Profile saved")

                room_name = f"room-{uuid.uuid4().hex[:4]}"
                participant_identity = customer["customer_id"]
                logger.info(f"{prefix} 📞 Initiating call to {customer['phone_number']}...")

                participant = await make_call(
                    phone_number=customer["phone_number"],
                    name=customer["customer_name"],
                    gender=customer["gender"],
                    sip_trunk_id=trunk_id,
                    room_name=room_name,
                    participant_identity=participant_identity
                )

                if participant:
                    logger.info(f"{prefix} ✅ Call successfully started (room: {room_name})")
                else:
                    logger.warning(f"{prefix} ⚠️ Call initiation failed or returned None")

            except Exception as e:
                logger.error(f"{prefix} ❌ Error during call: {e}", exc_info=True)
            finally:
                logger.info(f"{prefix} 📴 Call process ended")

    # ⚙️ Use rolling concurrency with semaphore + delay
    sem = asyncio.Semaphore(max_concurrent)
    tasks = []

    for idx, customer in enumerate(customers):
        task = asyncio.create_task(make_individual_call(customer, sem))
        tasks.append(task)

        if idx < len(customers) - 1:
            logger.info(f"⏱️ Waiting {delay_seconds}s before starting next call...")
            await asyncio.sleep(delay_seconds)

    await asyncio.gather(*tasks)
    logger.info("✅ All calls initiated successfully!")


# --------------------------
# Main
# --------------------------
if __name__ == "__main__":
    asyncio.run(run_calls_rec())
