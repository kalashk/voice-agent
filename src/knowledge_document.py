information = {
    "car_loan_detail": {
        "loan_types": [
        {
            "type": "PURCHASE CASE",
            "description": "यूज्ड कार खरीदने के लिए.",
            "max_loan_percentage": "कार की मार्केट वैल्यू का 90% तक.",
            "example": {
            "vehicle_market_value": "छह लाख",
            "max_funding_allowed": "90%",
            "max_loan_provided": "पांच लाख चालीस हज़ार"
            }
        },
        {
            "type": "REFINANCE CASE",
            "sub_types": [
            {
                "type": "NORMAL REFINANCE",
                "condition": "गाड़ी कैश में खरीदी गई हो या पुराना लोन 6 महीने से ज़्यादा पहले बंद हो गया हो.",
                "max_loan_percentage": "कार की मार्केट वैल्यू का 90% तक.",
                "example": {
                "vehicle_market_value": "छह लाख",
                "max_funding_allowed": "90%",
                "max_loan_provided": "पांच लाख चालीस हज़ार"
                }
            },
            {
                "type": "MULTIPLIER REFINANCE",
                "condition": "गाड़ी पर पुराना लोन 6 महीने से कम समय पहले बंद हुआ हो.",
                "max_loan_percentage": "कार की मार्केट वैल्यू का 80% से 140% तक.",
                "example": {
                "vehicle_market_value": "छह लाख",
                "max_funding_allowed": "140%",
                "max_loan_provided": "आठ लाख चालीस हज़ार"
                }
            },
            {
                "type": "BALANCE TRANSFER & TOPUP",
                "condition": "गाड़ी पर रनिंग लोन हो और कस्टमर को उसी गाड़ी पर एक्स्ट्रा फंड्स की ज़रूरत हो. पुराने लोन की कम से कम 9 ईएमआई बिना बाउंस के क्लियर होनी चाहिए.",
                "loan_tiers": [
                { "emis_paid": "9", "max_loan_percentage": "120%" },
                { "emis_paid": "10 or 11", "max_loan_percentage": "140%" },
                { "emis_paid": "12 or 17", "max_loan_percentage": "160%" },
                { "emis_paid": "18 or above", "max_loan_percentage": "200%" }
                ],
                "example": {
                "9_emi_paid": {
                    "max_loan_provided": "सात लाख बीस हज़ार"
                },
                "11_emi_paid": {
                    "max_loan_provided": "आठ लाख चालीस हज़ार"
                },
                "17_emi_paid": {
                    "max_loan_provided": "नौ लाख साठ हज़ार"
                },
                "18_emi_paid": {
                    "max_loan_provided": "बारह लाख"
                }
                }
            }
            ]
        }
        ],
        "terms_and_conditions": [
        "कस्टमर ने पिछले 3 महीनों में कोई पर्सनल या बिज़नेस लोन नहीं लिया हो.",
        "मिनिमम एवरेज बैंक बैलेंस एक महीने की ईएमआई के बराबर होना चाहिए.",
        "पिछले 3 महीनों में कोई ईएमआई बाउंस नहीं होनी चाहिए.",
        "टियर-3 व्हीकल्स (प्रोडक्शन बंद) पर मैक्सिमम 150% फंडिंग होती है; कुछ बैंक फंडिंग नहीं भी कर सकते हैं.",
        "आरओआई 11% से 17.5% तक वैरी करती है.",
        "परचेज़ के लिए गाड़ी की मैक्सिमम एज: 15 साल.",
        "रीफाइनेंस/बीटी के लिए गाड़ी की मैक्सिमम एज: 11 साल.",
        "मिनिमम लोन टेन्योर: 25 महीने, मैक्सिमम लोन टेन्योर: 60 महीने.",
        "कस्टमर के पास ओरिजिनल आरसी और कम से कम 90 दिनों की वैलिडिटी वाला इन्शुरन्स होना चाहिए."
        ],
        "emi_calculation": {
        "formula": "लोन अमाउंट, आरओआई और टेन्योर के हिसाब से ईएमआई कैलकुलेट होती है. हम आपको एक मोटा-मोटा आईडिया दे सकते हैं.",
        "emi_chart": {
            "roi_flat": "9%",
            "roi_reducing": "16%",
            "data": [
            { "loan_in_lacs": 1, "2_yr": 4896, "3_yr": 3516, "4_yr": 2834, "5_yr": 2432 },
            { "loan_in_lacs": 2, "2_yr": 9792, "3_yr": 7032, "4_yr": 5668, "5_yr": 4864 },
            { "loan_in_lacs": 3, "2_yr": 14688, "3_yr": 10548, "4_yr": 8502, "5_yr": 7296 },
            { "loan_in_lacs": 4, "2_yr": 19584, "3_yr": 14064, "4_yr": 11336, "5_yr": 9728 },
            { "loan_in_lacs": 5, "2_yr": 24480, "3_yr": 17580, "4_yr": 14170, "5_yr": 12160 },
            { "loan_in_lacs": 6, "2_yr": 29376, "3_yr": 21096, "4_yr": 17004, "5_yr": 14592 },
            { "loan_in_lacs": 7, "2_yr": 34272, "3_yr": 24612, "4_yr": 19838, "5_yr": 17024 },
            { "loan_in_lacs": 8, "2_yr": 39168, "3_yr": 28128, "4_yr": 22672, "5_yr": 19456 },
            { "loan_in_lacs": 9, "2_yr": 44064, "3_yr": 31644, "4_yr": 25506, "5_yr": 21888 },
            { "loan_in_lacs": 10, "2_yr": 48960, "3_yr": 35160, "4_yr": 28340, "5_yr": 24320 },
            { "loan_in_lacs": 11, "2_yr": 53856, "3_yr": 38676, "4_yr": 31174, "5_yr": 26752 },
            { "loan_in_lacs": 12, "2_yr": 58752, "3_yr": 42192, "4_yr": 34008, "5_yr": 29184 },
            { "loan_in_lacs": 13, "2_yr": 63648, "3_yr": 45708, "4_yr": 36842, "5_yr": 31616 },
            { "loan_in_lacs": 14, "2_yr": 68544, "3_yr": 49224, "4_yr": 39676, "5_yr": 34048 },
            { "loan_in_lacs": 15, "2_yr": 73440, "3_yr": 52740, "4_yr": 42510, "5_yr": 36480 },
            { "loan_in_lacs": 16, "2_yr": 78336, "3_yr": 56256, "4_yr": 45344, "5_yr": 38912 },
            { "loan_in_lacs": 17, "2_yr": 83232, "3_yr": 59772, "4_yr": 48178, "5_yr": 41344 },
            { "loan_in_lacs": 18, "2_yr": 88128, "3_yr": 63288, "4_yr": 51012, "5_yr": 43776 },
            { "loan_in_lacs": 19, "2_yr": 93024, "3_yr": 66804, "4_yr": 53846, "5_yr": 46208 },
            { "loan_in_lacs": 20, "2_yr": 97920, "3_yr": 70320, "4_yr": 56680, "5_yr": 48640 },
            { "loan_in_lacs": 21, "2_yr": 102816, "3_yr": 73836, "4_yr": 59514, "5_yr": 51072 },
            { "loan_in_lacs": 22, "2_yr": 107712, "3_yr": 77352, "4_yr": 62348, "5_yr": 53504 },
            { "loan_in_lacs": 23, "2_yr": 112608, "3_yr": 80868, "4_yr": 65182, "5_yr": 55936 },
            { "loan_in_lacs": 24, "2_yr": 117504, "3_yr": 84384, "4_yr": 68016, "5_yr": 58368 },
            { "loan_in_lacs": 25, "2_yr": 122400, "3_yr": 87900, "4_yr": 70850, "5_yr": 60800 }
            ]
        }
        }
    },
    "documents_required": {
        "essential_documents": [
        "के वाई सी डाक्यूमेंट्स: आधार कार्ड, पैन कार्ड, फोटो",
        "6 महीने का बैंक स्टेटमेंट",
        "व्हीकल डाक्यूमेंट्स: व्हीकल आरसी + इन्शुरन्स कॉपी",
        "एग्जिस्टिंग लोन: लोन अकाउंट स्टेटमेंट (एस ओ ए)"
        ],
        "documents_based_on_customer_profession": {
        "salaried employee": "3 महीने की सैलरी स्लिप + फॉर्म 16",
        "business": "2 साल की आई टी आर विद कम्प्यूटेशन + बिज़नेस प्रूफ जैसे जी एस टी / उद्यम रजिस्ट्रेशन",
        "farmer": "जमाबंदी रिसिप्ट"
        },
        "co_applicant": "अगर कस्टमर के पुराने लोन में को-एप्लीकेंट है, तो हमें को-एप्लीकेंट की के वाई सी भी लेनी है।"
    },
    "loan_eligibility": {
        "salaried": {
        "method": "एफ ओ आई आर बेस्ड कैलकुलेशन",
        "rule": "सैलरी का मैक्सिमम 70% ईएमआई के रूप में वापस किया जा सकता है. नया लोन, उपलब्ध एफ ओ आई आर पर निर्भर करता है."
        },
        "businessman": {
        "method": "इनकम डॉक्यूमेंट सरोगेट कैलकुलेशन",
        "rule": "कम एवरेज बैंक बैलेंस के मामले में, आई टी आर से इनकम को कंसीडर किया जाएगा, जो बिज़नेस से आई टी आर इनकम का मैक्सिमम 4एक्स हो सकता है."
        },
        "average_bank_balance": {
        "loan_up_to_10_lacs": "मिनिमम एवरेज बैंक बैलेंस ₹5,000 से ज़्यादा होना चाहिए.",
        "loan_above_10_lacs": "मंथली ईएमआई का 0.75एक्स से 1एक्स एवरेज बैंक बैलेंस चाहिए."
        }
    },
    "telecalling_psychology": [
      {
        "principle": "Reciprocity",
        "summary": "गिव एंड टेक: पहले कुछ वैल्यू दें, फिर कुछ मांगें.",
        "application": "लोन के फायदे पहले बताएं (जैसे पुराना लोन क्लियर और एक्स्ट्रा पैसे मिलेंगे)."
      },
      {
        "principle": "Social Proof",
        "summary": "जो सब करते हैं, वही सही: लोग दूसरों के एक्शन को फॉलो करते हैं.",
        "application": "बताएं कि बहुत से कस्टमर इस तरह के लोन ले रहे हैं."
      },
      {
        "principle": "Anchoring",
        "summary": "पहली बात का असर: पहली जानकारी से डिसीजन पर असर होता है.",
        "application": "शुरुआत में मैक्सिमम लोन अमाउंट बताएं ताकि बाद का ऑफर भी अच्छा लगे."
      },
      {
        "principle": "Loss Aversion",
        "summary": "नुकसान का डर: लोग फायदा उठाने से ज़्यादा नुकसान से बचना चाहते हैं.",
        "application": "लोन के बिना पैसों की ज़रूरत पूरी न होने के नुकसान को हाईलाइट करें."
      },
      {
        "principle": "Authority",
        "summary": "अथॉरिटी का सम्मान: लोग एक्सपर्ट की बात पर ज़्यादा भरोसा करते हैं.",
        "application": "खुद को एक भरोसेमंद बैंक प्रोफेशनल के रूप में पेश करें."
      },
      {
        "principle": "Scarcity Principle",
        "summary": "सीमित चीज़ें ज़्यादा पसंद आती हैं.",
        "application": "ऑफर की समय सीमा बताएं (जैसे 'यह रेट सिर्फ आज के लिए है')."
      },
      {
        "principle": "Urgency Principle",
        "summary": "जल्दबाजी के लिए प्रेरित करना.",
        "application": "प्रमोशन की आखिरी तारीख बताएं (जैसे 'प्रोसेसिंग फीस पर यह ऑफर सिर्फ महीने के आखिर तक है')."
      },
      {
        "principle": "Foot-in-the-Door Technique",
        "summary": "पहले छोटा रिक्वेस्ट, फिर बड़ा.",
        "application": "कॉल की शुरुआत में कस्टमर का नाम या गाड़ी की डिटेल पूछें."
      },
      {
        "principle": "Ben Franklin Effect",
        "summary": "जो आपके लिए फेवर करे, वो और फेवर करेगा.",
        "application": "कस्टमर से छोटी जानकारी लेकर उन्हें कन्वर्सेशन में एंगेज करें."
      }
    ],
    "guardrails": {
        "non_topic_questions": [
        "I am a financial consultant and my knowledge is limited to car loans. If you have any questions about car loans, I would be happy to help.",
        "माफ़ कीजिएगा, मैं सिर्फ कार लोन के बारे में जानकारी दे सकती हूं. क्या आप कार लोन के बारे में कुछ जानना चाहते हैं?",
        "मैं इस विषय पर जानकारी नहीं दे सकती. हमारा यह कॉल सिर्फ कार लोन से जुड़ा है. क्या मैं आपकी कार लोन के बारे में कोई मदद कर सकती हूँ?"
        ]
    },
    "sample_conversations": [
      {
        "id": "conversation_001",
        "product": "Used Car Loan",
        "consultant_name": 'kajal',
        "customer_name": "Shubham Kumar",
        "summary": "This is an introductory call to Shubham Kumar to offer a refinance loan on his 2022 model car. The customer is initially resistant as he already has a running loan and is struggling to repay it. He works as a laborer. The call ends with the consultant politely ending the call and offering to be contacted in the future.",
        "dialogue": [
          {
            "speaker": "consultant",
            "text": "Hello. जी नमस्कार sir."
          },
          {
            "speaker": "customer",
            "text": "नमस्कार जी."
          },
          {
            "speaker": "consultant",
            "text": "अब sir मेरी बात शुभम कुमार जी से हो रही है sir?"
          },
          {
            "speaker": "customer",
            "text": "बोलिए क्या काम पड़ गया शुभम कुमार जी से आपको?"
          },
          {
            "speaker": "consultant",
            "text": "Sir मुझे तो कुछ काम नहीं पड़ा काम तो आप ही का होने वाला है। मैं H D F C bank से मनराज बात कर रही हूं।"
          },
          {
            "speaker": "customer",
            "text": "कौन से bank से?"
          },
          {
            "speaker": "consultant",
            "text": "H D F C bank से sir."
          },
          {
            "speaker": "customer",
            "text": "H D F C bank से बोलिए madam."
          },
          {
            "speaker": "consultant",
            "text": "आप जो present time गाड़ी use कर रहे हैं ना 4 wheeler गाड़ी का number है 4769."
          },
          {
            "speaker": "customer",
            "text": "हां बोलिए आगे बोलिए."
          },
          {
            "speaker": "consultant",
            "text": "उसके ऊपर sir गाड़ी के ऊपर जो D finance का offer निकला है sir आपको करवाना हो तो बताइए."
          },
          {
            "speaker": "customer",
            "text": "क्या चीज़ है?"
          },
          {
            "speaker": "consultant",
            "text": "refinance का offer निकला है sir loan का offer अगर करवाना हो तो."
          },
          {
            "speaker": "customer",
            "text": "वह तो पहले भी loan पर है."
          },
          {
            "speaker": "consultant",
            "text": "Loan पर है?, आपके पास तो दो हज़ार बाइस का model है ना."
          },
          {
            "speaker": "customer",
            "text": "हैं?"
          },
          {
            "speaker": "consultant",
            "text": "दो हज़ार बाइस का model है ना यह तो."
          },
          {
            "speaker": "customer",
            "text": "हां."
          },
          {
            "speaker": "consultant",
            "text": "तो इसके ऊपर तो मतलब यह loan चलते हुए दो साल से ज़्यादा हो गया मतलब चल ही रहा है."
          },
          {
            "speaker": "customer",
            "text": "हां तो loan तो जैसे जैसे पैसे आ रहे हैं किश्त आ रही है वैसे वैसे दे भी रहे हैं."
          },
          {
            "speaker": "consultant",
            "text": "हां वो तो दे रहे हैं फिर मैंने मान लिया but यह kitne साल के लिए लिया था आपने वो पहले वाले?"
          },
          {
            "speaker": "customer",
            "text": "मैंने पांच साल के लिए लिया था."
          },
          {
            "speaker": "consultant",
            "text": "पांच साल के लिए लिया था तो फिर आपको अभी जैसे पैसों की requirement हो तो आप दोबारा ले सकते हो इससे मैं जो आपकी गाड़ी की insurance value है ना sir."
          },
          {
            "speaker": "customer",
            "text": "नहीं नहीं madam और नहीं लेना यह मुश्किल से चुकाया जा रहा है क्या अभी नहीं करते."
          },
          {
            "speaker": "consultant",
            "text": "क्या करते हो sir आप?"
          },
          {
            "speaker": "customer",
            "text": "करते तो वैसे ही मजदूरी करते हैं इधर उधर बस हो कर."
          },
          {
            "speaker": "consultant",
            "text": "ठीक है sir. In future आपको जैसे requirement हो personal loan decision हो तो फिर आप ही number पर call कर सकते हैं."
          },
          {
            "speaker": "customer",
            "text": "इसी number पर?"
          },
          {
            "speaker": "consultant",
            "text": "जी sir."
          },
          {
            "speaker": "customer",
            "text": "आपका number है यह?"
          },
          {
            "speaker": "consultant",
            "text": "यह bank का number है?"
          },
          {
            "speaker": "consultant",
            "text": "Sir आपको loan के regarding बात करनी होगी तो इससे मेरे से बात हो जाएगी उससे."
          },
          {
            "speaker": "customer",
            "text": "अच्छा आपसे बात हो रही है आपका शुभ नाम जान सकता हूं मैं?"
          },
          {
            "speaker": "consultant",
            "text": f"Sir 'kajal'."
          },
          {
            "speaker": "customer",
            "text": f"'kajal', ठीक है mam. Ok. Thank you sir."
          }
        ],
        "analysis": f"The consultant, 'kajal', attempts to sell a refinance loan. The customer, Shubham, is resistant, citing financial difficulties and an existing loan. The consultant's attempt to sell is met with firm refusal. The conversation highlights common customer objections (already in debt, struggling with payments) and the need for a graceful exit from the call."
      },
      {
        "id": "conversation_002",
        "product": "Used Car Loan (Refinance)",
        "consultant_name": f"'kajal'",
        "customer_name": "Vishnu Dev",
        "summary": f"The consultant, 'kajal', calls Vishnu Dev to offer a refinance loan on his 2022 Eeco 5-seater. The customer is initially interested but has a running loan. The consultant explains the refinance concept and the high loan amount possible (up to double the car's value) and addresses the customer's income and payment history. The customer, a self-employed supplier of snacks, shows interest in the interest rate, and the call concludes with the consultant asking him to call back.",
        "dialogue": [
          {
            "speaker": "consultant",
            "text": "Hello. Hello. जी नमस्कार sir."
          },
          {
            "speaker": "customer",
            "text": "नमस्कार जी."
          },
          {
            "speaker": "consultant",
            "text": "Sir मेरी बात विष्णु देव जी से हो रही है sir?"
          },
          {
            "speaker": "customer",
            "text": "हां जी."
          },
          {
            "speaker": "consultant",
            "text": "Sir मैं H D F C bank से मद्रास बात कर रही हूं sir. आप जो sir present time गाड़ी use कर रहे हैं ना 4 wheeler eco 5 star."
          },
          {
            "speaker": "customer",
            "text": "हां जी."
          },
          {
            "speaker": "consultant",
            "text": "इसके ऊपर sir re finance का offer निकला हैं अगर आपको करवाना हो तो बताइए sir."
          },
          {
            "speaker": "customer",
            "text": "क्या निकला हुआ है?"
          },
          {
            "speaker": "consultant",
            "text": "Refinance car loan का offer है sir आपको करवाना हो तो बताइए."
          },
          {
            "speaker": "customer",
            "text": "Loan? कौन सा loan?"
          },
          {
            "speaker": "consultant",
            "text": "Car loan का sir."
          },
          {
            "speaker": "customer",
            "text": "Loan एक चल ही रहा है madam."
          },
          {
            "speaker": "consultant",
            "text": "चल रहा हैं, vo तो sir पहले का चल रहा था, आपके पास तो दो हज़ार बाइस का model हैं, तो वो पहले का दो साल से चल रहा हैं sir."
          },
          {
            "speaker": "customer",
            "text": "हांं दो साल हो गया."
          },
          {
            "speaker": "consultant",
            "text": "हांं तो sir उसके ऊपर आप जैसे दोबारा लेना चाहेंगे तो ले सकते हो जैसे आपकी जो गाड़ी की value हैं ना, उसके दो गुना तक आपको loan मिल जाएगा. double है ना. उसमें sir जो पहले का आपका loan चल रहा है ना वो complete हो कर और आपकी गाड़ी free हो जाएगी बाकी जो amount बचेगा वो आपके account में आ जाएंगे sir."
          },
          {
            "speaker": "customer",
            "text": "हां पैसे में?"
          },
          {
            "speaker": "consultant",
            "text": "हां."
          },
          {
            "speaker": "customer",
            "text": "क्या करते क्या हो sir आप?"
          },
          {
            "speaker": "consultant",
            "text": "हम namkeen business करते हैं supply करते हैं."
          },
          {
            "speaker": "customer",
            "text": "क्या?"
          },
          {
            "speaker": "consultant",
            "text": "क्या sir? namkeen business करते हैं, supply करते हैं नमकीन, नमकीन गुजिया."
          },
          {
            "speaker": "consultant",
            "text": "अच्छा तो sir आपकी shop होगी? kitna कमा लेते हो आप?"
          },
          {
            "speaker": "customer",
            "text": "महीने का साठ हज़ार सत्तर हज़ार हो जाते हैं madam."
          },
          {
            "speaker": "consultant",
            "text": "अच्छा साठ, सत्तर हज़ार हो जाते हैं तो अच्छा तो पहले की किस्त तो आप लगातार दे रहे हो ना beach में due to nahi hui कोई किस्त?"
          },
          {
            "speaker": "customer",
            "text": "नहीं नहीं हुई थी एक बार भी नहीं हुई."
          },
          {
            "speaker": "consultant",
            "text": "एक बार भी नहीं हुई हां तो वह किस bank से चल रहा हैं पहले का?"
          },
          {
            "speaker": "customer",
            "text": "हां जी."
          },
          {
            "speaker": "consultant",
            "text": "पहले का जो आपका loan चल रहा हैं वह किस bank से चल रहा है?"
          },
          {
            "speaker": "customer",
            "text": "वह चोयला से चल रहा हैं madam."
          },
          {
            "speaker": "consultant",
            "text": "महिंद्रा से?"
          },
          {
            "speaker": "customer",
            "text": "चोयला चोयला."
          },
          {
            "speaker": "consultant",
            "text": "अच्छा हां तो sir देख लीजिए अगर आपको करवाना हो तो sir आप करवा सकते हो."
          },
          {
            "speaker": "customer",
            "text": "उसमें कितने तक ब्याज मुझे पहले बता दो जब हमें पता लगेगा."
          },
          {
            "speaker": "consultant",
            "text": "हां ब्याज sir इसमें रहेगा जिसमें percent के हिसाब से रहता है तो आठ से नौ percent बाकी पैसा के हिसाब से लगता है तो चित्र पचहत्तर पैसा से एक tak लगता है sir."
          },
          {
            "speaker": "customer",
            "text": "चत्तर पैत्तर पै लगता हैं sir. Phone कर देना sir यह number पर ना. ठीक हैं. ठीक हैं अच्छा."
          }
        ],
        "analysis": "The consultant successfully explains the refinance offer to the customer, Vishnu Dev, despite an initial objection about an existing loan. The consultant provides a clear benefit (higher loan amount and single EMI) and successfully transitions the conversation to the customer's professional details and flawless repayment history. The customer, who is self-employed, shows interest in the interest rate, but the conversation ends abruptly with no clear commitment."
      },
      {
        "id": "conversation_003",
        "product": "Used Car Loan (Refinance)",
        "consultant_name": f"'kajal'",
        "customer_name": "Sitaram Parikh",
        "summary": f"The consultant, 'kajal', calls Sitaram Parikh to offer a refinance loan on his 2022 I20. The customer expresses resistance and confusion over the need for a new loan since he already has one. The consultant explains the 'balance transfer and top-up' feature, but the customer remains skeptical about the financial benefits. He ultimately rejects the offer, and the call ends politely.",
        "dialogue": [
          {
            "speaker": "consultant",
            "text": "Hello. Hello जी नमस्कार sir."
          },
          {
            "speaker": "customer",
            "text": "नमस्कार."
          },
          {
            "speaker": "consultant",
            "text": "Sir मेरी बात सीताराम पारिख जी से हो रही है sir?"
          },
          {
            "speaker": "customer",
            "text": "कौन बोल रहे हो?"
          },
          {
            "speaker": "consultant",
            "text": "Sir मैं H D F C bank से मद्रास बात कर रही हूं sir."
          },
          {
            "speaker": "customer",
            "text": "जी."
          },
          {
            "speaker": "consultant",
            "text": "आप जो present time गाड़ी use कर रहे हैं ना sir 4 wheeler I 20?"
          },
          {
            "speaker": "customer",
            "text": "हां."
          },
          {
            "speaker": "consultant",
            "text": "उसके ऊपर से refinance का offer निकला है sir आपको करवाना हो तो बताइए sir."
          },
          {
            "speaker": "customer",
            "text": "क्या करना है?"
          },
          {
            "speaker": "consultant",
            "text": "Refinance का offer निकला है sir आपको करवाना हो तो बताइए. Car loan का offer है sir."
          },
          {
            "speaker": "customer",
            "text": "Car loan तो लिया हुआ है उसके ऊपर."
          },
          {
            "speaker": "consultant",
            "text": "लिया हुआ है, तो फिर दो हज़ार बाइस का model है ना आपके पास तो."
          },
          {
            "speaker": "customer",
            "text": "हैं?"
          },
          {
            "speaker": "consultant",
            "text": "तो sir इसके ऊपर जैसे दो साल हो गए इस loan को हुए, तो आप इसके ऊपर दुबारा ले सकते हो sir."
          },
          {
            "speaker": "customer",
            "text": "क्या?"
          },
          {
            "speaker": "consultant",
            "text": "इसमें sir जो गाड़ी की insurance value ना आपकी."
          },
          {
            "speaker": "customer",
            "text": "हां."
          },
          {
            "speaker": "consultant",
            "text": "उसके दो गुना तक आपको loan provide होगा sir."
          },
          {
            "speaker": "customer",
            "text": "हां."
          },
          {
            "speaker": "consultant",
            "text": "तो उसमें sir जो पहले का loan चल रहा है ना वह clear हो कर और बाकी का जो amount रहेगा ना वह आपके account में आएगा sir."
          },
          {
            "speaker": "customer",
            "text": "हां."
          },
          {
            "speaker": "consultant",
            "text": "जी sir, ऐसा रहेगा बाकी जो पहले का loan चल रहा है ना वह आपका बिल्कुल clear होगा."
          },
          {
            "speaker": "customer",
            "text": "हां."
          },
          {
            "speaker": "consultant",
            "text": "और बाकी जो बच जाएगा वो amount आपके account में आ जाएगा फिर ऐसा होगा."
          },
          {
            "speaker": "customer",
            "text": "उसका interest क्या है?"
          },
          {
            "speaker": "consultant",
            "text": "Interest sir आठ से नौ percent."
          },
          {
            "speaker": "customer",
            "text": "फ़ायदा क्या हुआ?"
          },
          {
            "speaker": "consultant",
            "text": "फ़ायदा तो sir यही है कि मतलब आपको requirement hogi पैसों की तो आपके account में कुछ थोड़े बहुत पैसे आ जाएंगे बाकी जो पहले का loan है वो clear हो जाएगा आपकी गाड़ी free हो जाएगी वैसे तो."
          },
          {
            "speaker": "customer",
            "text": "free कहां हुई आप paise loge na madam? क्या?"
          },
          {
            "speaker": "consultant",
            "text": "Installment आप शुरू कर दोगे?"
          },
          {
            "speaker": "customer",
            "text": "हम तो कर देंगे फिर वह आपके account में भी तो आ रहा ना कुछ balance तो ऐसे तो है नहीं कि बिल्कुल 0 हो गया वो."
          },
          {
            "speaker": "consultant",
            "text": "कितना balance हो जाएगा? क्या?"
          },
          {
            "speaker": "customer",
            "text": "नहीं लेना madam."
          },
          {
            "speaker": "consultant",
            "text": "नहीं लेना?"
          },
          {
            "speaker": "customer",
            "text": "जी."
          },
          {
            "speaker": "consultant",
            "text": "फिर से in future आपको किसी का भी requirement हो किसी loan की जैसे personal loan की चीज़ हो तो आप इस number पर phone कर सकते हो sir."
          }
        ],
        "analysis": f"The consultant, 'kajal', attempts to sell a refinance loan to Sitaram Parikh. The customer is skeptical from the beginning, highlighting that he already has a loan and sees no clear benefit. Despite the consultant explaining the 'balance transfer and top-up' feature and a low-interest rate, the customer remains unconvinced, pointing out that he would still have a new installment. The conversation ends with the customer's polite refusal, showcasing the importance of quickly identifying a customer's disinterest and offering a graceful exit while keeping the door open for future contact."
      },
      {
        "id": "conversation_004",
        "product": "Used Car Loan (Refinance)",
        "consultant_name": f"'kajal'",
        "customer_name": "Akshay Singh",
        "summary": f"The consultant, 'kajal', calls Akshay Singh to offer a refinance loan on his car. The customer is a cautious and informed buyer who already has a running loan on a 2022 model car. He questions the new interest rate compared to his existing one, expresses skepticism about the benefits, and ultimately rejects the offer. The conversation highlights the customer's focus on the bottom line (interest rate and cost) and the consultant's persistence.",
        "dialogue": [
          {
            "speaker": "consultant",
            "text": "Hello. Hello जी नमस्कार sir."
          },
          {
            "speaker": "customer",
            "text": "नमस्कार जी."
          },
          {
            "speaker": "consultant",
            "text": "Sir मेरी बात अक्षय सिंह जी से हो रही हैं sir?"
          },
          {
            "speaker": "customer",
            "text": "हांं जी."
          },
          {
            "speaker": "consultant",
            "text": "Sir मैं H D F C bank से मनराज बात कर रही हूं sir."
          },
          {
            "speaker": "customer",
            "text": "हांं जी बोलो."
          },
          {
            "speaker": "consultant",
            "text": "आप जो present time गाड़ी use कर रहे हैं ना sir 4 wheeler."
          },
          {
            "speaker": "customer",
            "text": "हांं जी हां."
          },
          {
            "speaker": "consultant",
            "text": "गाड़ी का number sir 1760. हां. उसके ऊपर refinance का offer निकला हैं अगर आपको करवाना हैं तो बताइए sir."
          },
          {
            "speaker": "customer",
            "text": "क्या charge होगा? क्या charge होगा sir?"
          },
          {
            "speaker": "consultant",
            "text": "अभी गाड़ी finance में हैं या finance पर ही हैं?"
          },
          {
            "speaker": "customer",
            "text": "Finance हैं. Finance हैं."
          },
          {
            "speaker": "consultant",
            "text": "Finance हैं तो sir जो आपकी गाड़ी की insurance value हैं ना उसके दो गुना तक मतलब double तक loan provide हो जाएगा आपको. इसमें sir जो पहले का loan चल रहा हैं ना आपका वह clear हो जाएगा और बाकि का amount रहेगा वह आपके account में आएगा sir."
          },
          {
            "speaker": "customer",
            "text": "कितना charge क्या होगा फिर? ब्याज क्या charge होगा?"
          },
          {
            "speaker": "consultant",
            "text": "ब्याज sir आठ से नौ percent रहेगा sir."
          },
          {
            "speaker": "customer",
            "text": "हैं?"
          },
          {
            "speaker": "consultant",
            "text": "आठ से नौ percent रहेगा sir ब्याज."
          },
          {
            "speaker": "customer",
            "text": "यह pehele से मेरे को कम लगा हुआ tha ब्याज, abhi से."
          },
          {
            "speaker": "consultant",
            "text": " कितना लगा? हैं?"
          },
          {
            "speaker": "customer",
            "text": "छह percent हैं, छह percent हैं."
          },
          {
            "speaker": "consultant",
            "text": "छह percent हैं तो sir वह आपने वह तो sir आपने नई गाड़ी ली थी ना उस time."
          },
          {
            "speaker": "customer",
            "text": "हां."
          },
          {
            "speaker": "consultant",
            "text": "तो उस पर तो वैसे ही कम लगता हैं sir नई गाड़ी पर तो हम भी sir 5 percent तक ही देते हैं मतलब पचास पैसे के हिसाब से ही देते हैं."
          },
          {
            "speaker": "customer",
            "text": "हां."
          },
          {
            "speaker": "consultant",
            "text": "तो अब दो साल हो गया आपका दो हज़ार बाइस का model हैं आपके पास."
          },
          {
            "speaker": "customer",
            "text": "हां."
          },
          {
            "speaker": "consultant",
            "text": "तो इसमें."
          },
          {
            "speaker": "customer",
            "text": "कैसे enquiry आती हैं यह इसका कैसे पता चलता हैं आपको?"
          },
          {
            "speaker": "consultant",
            "text": "हमें कैसे पता चलता हैं sir? हमारे पास data आता हैं sir."
          },
          {
            "speaker": "customer",
            "text": "हैं?"
          },
          {
            "speaker": "consultant",
            "text": "पूरा data आता हैं sir हमारे पास."
          },
          {
            "speaker": "customer",
            "text": "हां."
          },
          {
            "speaker": "consultant",
            "text": "वह company वाले देते हैं हमें फिर हम जिसको यह loan की requirement होती है वह हम bank वालों को file भेजते हैं फिर bank वाले उनके account में पैसे डालते हैं loan provide हो जाता है उनको. हां. ऐसा होता है sir और जिस भी bank से कम ब्याज लगता है ना हम उस bank से करवा देते हैं."
          },
          {
            "speaker": "customer",
            "text": "हैं?"
          },
          {
            "speaker": "consultant",
            "text": "अब जिस भी bank से कम ब्याज लगता है ना हम उस bank से करवा देते हैं उनका loan."
          },
          {
            "speaker": "customer",
            "text": "हां."
          },
          {
            "speaker": "consultant",
            "text": "सब सब bank का अलग अलग यह ब्याज लगता है sir सबका same rate पर होता है नहीं."
          },
          {
            "speaker": "customer",
            "text": "चलो ठीक है जी मेरे को नहीं चाहिए."
          },
          {
            "speaker": "consultant",
            "text": "नहीं चाहिए ठीक है फिर in future आपको requirement है जैसे personal loan business loan तो आप phone कर सकते हैं फिर number पर."
          },
          {
            "speaker": "customer",
            "text": "ठीक ठीक."
          },
          {
            "speaker": "consultant",
            "text": "Thank you sir."
          }
        ],
        "analysis": f"The consultant, 'kajal', attempts to sell a refinance loan to Akshay Singh. The customer is initially interested in the details but is immediately skeptical when the new interest rate is revealed to be higher than his current one. The consultant attempts to justify the higher rate by explaining the difference between new and used car loans. The customer then questions how the consultancy gets their information. The conversation ultimately ends in a rejection, highlighting the customer's cost-consciousness and skepticism towards cold calls. The consultant ends the call politely, keeping the door open for future business."
      },
      {
        "id": "conversation_005_strategic",
        "product": "Used Car Loan (Refinance)",
        "consultant_name": f"'kajal'",
        "customer_name": "Akshay Singh",
        "summary": f"This is a strategic conversation where the consultant, 'kajal', first asks a series of qualifying questions to understand the customer's exact needs and financial situation. She then uses this information to build a personalized loan offer, which makes the customer feel understood and valued. 'kajal' leverages sales tactics like 'need-finding' and 'value-based selling' to close the deal effectively.",
        "dialogue": [
          {
            "speaker": "consultant",
            "text": "Hello. Hello ji namaskar sir."
          },
          {
            "speaker": "customer",
            "text": "Namaskar ji."
          },
          {
            "speaker": "consultant",
            "text": "Sir meri baat Akshay Singh ji se ho rahi hai?"
          },
          {
            "speaker": "customer",
            "text": "Haan ji."
          },
          {
            "speaker": "consultant",
            "text": f"Sir main H D F C Bank se 'kajal' baat kar rahi hoon. Sir, aap jo present time gaadi use kar rahe hain, Swift VXi 2022 model, uska number 1760 hai? Ispe ek special refinance offer aaya hai. Kya abhi gaadi pe loan chal raha hai ya free hai?"
          },
          {
            "speaker": "customer",
            "text": "Finance hai."
          },
          {
            "speaker": "consultant",
            "text": "Theek hai sir. Is offer se aapki gaadi ki market value ka double tak loan mil sakta hai. Sir, iski poori detail batane se pehle, main aapse kuch sawal puch sakti hoon? Isse main aapke liye best deal nikaal paungi."
          },
          {
            "speaker": "customer",
            "text": "Puchiye."
          },
          {
            "speaker": "consultant",
            "text": "Sabse pehle, sir, aapka loan kis bank se chal raha hai? Aur abhi uski kitni EMI baki hain?"
          },
          {
            "speaker": "customer",
            "text": "Loan to H D F C Bank se hi hai. Aur 17 EMI's de chuka hoon."
          },
          {
            "speaker": "consultant",
            "text": "Bahut badhiya sir! Iska matlab hai ki aapka loan account kaafi purana hai aur history achchi hai. Sir, aapki EMI kitni aati hai, agar bata payein?"
          },
          {
            "speaker": "customer",
            "text": "Lagbhag ₹12,000."
          },
          {
            "speaker": "consultant",
            "text": "Got it. Sir, kya aapko refinance ke saath koi extra funds ki zaroorat hai, jaise business ya personal use ke liye? Ya aap sirf purane loan ko band karana chahte hain?"
          },
          {
            "speaker": "customer",
            "text": "Mujhe personal use ke liye kuch extra paisa chahiye. Par aapka byaaj to mere existing loan se zyada hoga?"
          },
          {
            "speaker": "consultant",
            "text": "Sir, main aapki baat samajh sakti hoon. Nayi gaadi ka rate kam hota hai. Lekin, kya aapko lagta hai ki aapko personal loan ya business loan mil sakta hai itna bada amount, aur woh bhi kam byaaj rate par? Personal loan aur business loan ka interest rate 18-24% tak hota hai. Yahan, hum aapko sirf **11-16%** mein, ek hi loan mein, dono fayde de rahe hain—**old loan close** aur **extra cash**."
          },
          {
            "speaker": "customer",
            "text": "Hmm, ye baat to theek hai. Toh kitna loan mil jayega?"
          },
          {
            "speaker": "consultant",
            "text": "Jaisa ki aapne bataya, aapki gaadi 2022 model hai, to market value approx ₹6 lakh hai. Aur aapne 17 EMI's bhi di hain, to aapko **160%** tak ka loan mil sakta hai, yaani **₹9.6 lakh**. Ismein aapka purana loan clear ho jayega aur lagbhag ₹6 lakh aapke account mein aa jayenge. Aapko EMI ₹25,506 (48 months) ya ₹19,456 (60 months) ke aas paas padegi. Aapko konsi EMI comfortable rahegi, sir?"
          },
          {
            "speaker": "customer",
            "text": "₹19,000 wali theek hai. Par itne paise kaise milenge?"
          },
          {
            "speaker": "consultant",
            "text": "Sir, iske liye humein kuch documents chahiye. Sir, aap salaried hain ya business karte hain?"
          },
          {
            "speaker": "customer",
            "text": "Main salaried hoon. IT mein job karta hoon."
          },
          {
            "speaker": "consultant",
            "text": "Excellent sir. Salaried hain to process bahut smooth hai. Main aapko documents ki list WhatsApp par bhej rahi hoon—KYC, 6-mahine ka bank statement, salary slips, Form 16 aur gaadi ke documents. Jaise hi aap share karenge, main aapka process aage badha doongi."
          },
          {
            "speaker": "customer",
            "text": "Theek hai, aap list bhej do. Main check karke send karta hoon."
          }
        ],
        "analysis": f"'kajal''s approach is highly effective. She starts by asking qualifying questions to understand the customer's needs, rather than just pushing a product. This 'needs-based selling' allows her to tailor the pitch perfectly. When the customer raises an objection about the interest rate, she doesn't just dismiss it; she uses a **comparative selling** tactic. By comparing her offer to personal and business loans, she justifies the higher interest rate of the used car loan as a more cost-effective and beneficial option. She uses concrete numbers (9.6 lakh loan, 6 lakh cash-in-hand) to make the offer tangible and appealing. Finally, she provides a clear call to action with a well-defined list of documents, securing a firm commitment from the customer."
      },
      {
        "id": "conversation_purchase_001",
        "product": "Used Car Loan (Purchase Case)",
        "consultant_name": "Rohan",
        "customer_name": "Amit Sharma",
        "summary": "The consultant, Rohan, successfully convinces Amit, a customer looking to buy a used car in cash, to opt for a loan instead. Rohan uses a value-based selling approach, highlighting the benefits of retaining cash for other investments and the low-cost nature of a car loan compared to other financial products. He addresses the customer's concerns about interest and processing fees and closes the deal by securing a commitment to send documents.",
        "dialogue": [
          {
            "speaker": "consultant",
            "text": "Hello, Amit ji. Main Rohan, Axis Bank se baat kar raha hoon. Aapne ek used car purchase ke liye enquiry daali thi, Maruti Swift VXi, 2022 model, right?"
          },
          {
            "speaker": "customer",
            "text": "Haan, theek hai. Main us gaadi ke liye interested hoon. Par main cash mein lene ka soch raha hoon."
          },
          {
            "speaker": "consultant",
            "text": "Bahut accha hai sir. Par main aapko ek behtar option de sakta hoon jisse aapke paise bhi bachenge. Kya aap ek minute sun sakte hain?"
          },
          {
            "speaker": "customer",
            "text": "Bataiye, kya offer hai?"
          },
          {
            "speaker": "consultant",
            "text": "Sir, aapki gaadi ki market value approx ₹6 lakh hai. Agar aap loan lete hain, to aapko ₹5.4 lakh tak ka loan mil jayega (90% of market value). Isse aapka ₹5.4 lakh ka cash aapke paas hi rahega. Aap use business ya kisi investment mein laga sakte hain, jahan returns is car loan ke byaaj se bhi zyada honge."
          },
          {
            "speaker": "customer",
            "text": "Interest kitna lagega? Aur kya yeh itna faydemand hai?"
          },
          {
            "speaker": "consultant",
            "text": "Sir, byaaj 13-16% reducing rate par hai, jo ki personal loan ya business loan se bahut kam hai. For example, personal loan par 18-24% tak byaaj lagta hai. Yahan, ₹5.4 lakh ke loan par, 5 saal ki EMI ₹13,133 hogi. Aap sochiye, itna bada amount aapke paas hi rahega, aur mahine ki ek choti si EMI se aapki car bhi aa jayegi. Kya aapko yeh option sahi lag raha hai, sir?"
          },
          {
            "speaker": "customer",
            "text": "Processing fee kya hogi?"
          },
          {
            "speaker": "consultant",
            "text": "Sir, 2-3% processing fee hoti hai, lekin jo aapka cash bachega, usse aapka ROI kitna badh sakta hai, aap sochiye. Apne paise ko free rakhna hamesha ek smart financial move hota hai."
          },
          {
            "speaker": "customer",
            "text": "Hmm, theek hai. Process kitne din mein ho jayega?"
          },
          {
            "speaker": "consultant",
            "text": "Sir, 5-6 din mein poora process ho jayega. Bas aapko kuch documents dene honge. Aap salaried hain ya business karte hain?"
          },
          {
            "speaker": "customer",
            "text": "Main salaried hoon. Private job hai."
          },
          {
            "speaker": "consultant",
            "text": "Theek hai sir. Main documents ki list WhatsApp kar raha hoon. Aapko bas KYC, bank statement aur salary slips dene honge. Kya aap abhi documents bhej sakte hain?"
          },
          {
            "speaker": "customer",
            "text": "Ok, main list dekh ke bhejta hoon. Process shuru karwa do."
          }
        ],
        "analysis": "Rohan successfully converts a cash buyer into a loan customer by using a **value-based sales pitch**. He re-frames the conversation from 'cost of loan' to 'value of liquidity'. By highlighting the high interest rates of other loan products and the potential returns on saved cash, he creates a compelling argument. He addresses the customer's objection about the processing fee directly by comparing it to the financial gains. The call ends with a clear commitment from the customer, indicating a successful close."
      },
      {
        "id": "conversation_normal_refinance_002_modified",
        "product": "Used Car Loan (Normal Refinance)",
        "consultant_name": f"'kajal'",
        "customer_name": "Sanjay Kapoor",
        "summary": f"'kajal', the consultant, engages Sanjay in a detailed, back-and-forth conversation to sell a refinance loan. She starts by gently probing for a need, then slowly reveals the loan's benefits, ensuring the customer follows along at each step. She successfully counters objections about the necessity of a loan by positioning it as a strategic financial tool for business growth and as a safety net. The conversation is less of a sales pitch and more of a consultation, which leads to a successful deal.",
        "dialogue": [
          {
            "speaker": "consultant",
            "text": "Hello, namaskar. Meri baat Sanjay Kapoor ji se ho rahi hai?"
          },
          {
            "speaker": "customer",
            "text": "Haan ji, main bol raha hoon. Kaun?"
          },
          {
            "speaker": "consultant",
            "text": f"Sir, main 'kajal', ICICI Bank se baat kar rahi hoon. Maine aapko aapki Maruti Swift VXi, 2022 model, ke liye call kiya hai. Kya aap abhi bhi wohi gaadi use kar rahe hain?"
          },
          {
            "speaker": "customer",
            "text": "Haan, main hi use kar raha hoon. Kya hua?"
          },
          {
            "speaker": "consultant",
            "text": "Sir, ek chhota sa offer hai hamare paas aapki gaadi ke liye. Sir, is gaadi par abhi koi loan chal raha hai ya loan close ho chuka hai?"
          },
          {
            "speaker": "customer",
            "text": "Haan, mera purana loan to pichle saal hi band ho gaya tha. Abhi mujhe koi loan nahi chahiye."
          },
          {
            "speaker": "consultant",
            "text": "Theek hai sir. Toh aapki gaadi bilkul free hai. Sir, ismein aapka CIBIL score bhi kaafi strong hoga. Kya main sahi keh rahi hoon?"
          },
          {
            "speaker": "customer",
            "text": "Haan, shayad 800 ke aas-paas hoga. Par iska loan se kya lena-dena?"
          },
          {
            "speaker": "consultant",
            "text": "Sir, CIBIL score accha hone ka matlab hai ki banks aapko trust karte hain aur aapke liye special offers nikaalte hain. Ek aisa hi refinance offer hamare paas hai. Sir, aapka koi business hai, right?"
          },
          {
            "speaker": "customer",
            "text": "Haan, business hai. Par abhi funds ki koi zaroorat nahi hai. Waise, kya offer hai?"
          },
          {
            "speaker": "consultant",
            "text": "Sir, is offer mein, jo aapki gaadi ki market value hai, uska 90% tak loan mil sakta hai. Kya aapko lagta hai ki aapke business mein ya personal life mein kabhi emergency funds ki zaroorat pad sakti hai?"
          },
          {
            "speaker": "customer",
            "text": "Aise to kuch bhi ho sakta hai. Par loan leke kya faayda?"
          },
          {
            "speaker": "consultant",
            "text": "Sir, is loan ka sabse bada faayda ye hai ki aapka paisa aapke paas rahega. ₹6 lakh ki gaadi hai, to ₹5.4 lakh tak ka loan aapko mil jayega. Is paise ko aap apni savings mein rakh sakte hain ya business mein laga sakte hain. Kya aapko ye idea theek lag raha hai?"
          },
          {
            "speaker": "customer",
            "text": "Byaaj kya lagega? Aur agar zaroorat nahi hai, to byaaj kyu doon?"
          },
          {
            "speaker": "consultant",
            "text": "Sir, bahut hi valid point hai. Iska byaaj 13% se 16% hai. Par aap sochiye, agar aapko kabhi business ke liye ₹5 lakh ki zaroorat padti hai, to aap personal loan lenge, jismein byaaj 18-24% hota hai. Yahan aapka byaaj kam hai, tenure 5 saal tak ka hai, aur funds aapke haath mein hain. Kya yeh ek smart move nahi hai?"
          },
          {
            "speaker": "customer",
            "text": "Haan, thoda sahi lag raha hai. Par yeh offer kab tak hai?"
          },
          {
            "speaker": "consultant",
            "text": "Sir, is offer ki validity limited hai, isliye humne aapko khud call kiya hai. Aise schemes baar-baar nahi aati. Agar aapko kal ko zaroorat padti hai, to aapko new application process karna hoga, jismein terms and conditions alag ho sakti hain."
          },
          {
            "speaker": "customer",
            "text": "Ok, theek hai. EMI kya aayegi?"
          },
          {
            "speaker": "consultant",
            "text": "Sir, ₹5.4 lakh ke loan par 5 saal ke liye EMI ₹13,133 hogi. Yeh aapke business ke liye bahut hi affordable figure hai. Kya main aage ka process shuru karoon, documents ke saath?"
          },
          {
            "speaker": "customer",
            "text": "Theek hai, process shuru karo. Kya documents chahiye honge?"
          }
        ],
        "analysis": f"The conversation is highly effective due to its back-and-forth, consultative nature. Instead of just stating facts, 'kajal' asks questions to understand the customer's mindset. She uses **reflective listening** ('Theek hai sir. Toh aapki gaadi bilkul free hai.') and **needs-based selling** ('Kya aapko future mein koi business expansion ya personal zaroorat ke liye funds chahiye honge?'). By slowly building her case, she educates the customer about the value of the loan as a financial asset. She successfully counters the objection about interest by comparing it to more expensive alternatives and uses **FOMO** to create a sense of urgency, leading to a successful and well-informed close."
      },
      {
        "id": "conversation_balance_transfer_003_rapid",
        "product": "Used Car Loan (Balance Transfer & Topup)",
        "consultant_name": f"'kajal'",
        "customer_name": "Prakash Kumar",
        "summary": f"This is a fast-paced, highly interactive conversation where 'kajal', the consultant, uses a rapid back-and-forth dialogue to sell a 'Balance Transfer & Topup' loan. He breaks down the pitch into small, digestible chunks, ensuring the customer is engaged and understands each point. The high frequency of dialogues helps build immediate rapport and addresses every minor question, leading to a quick and successful close.",
        "dialogue": [
          {
            "speaker": "consultant",
            "text": f"Hello, namaste Prakash ji. Main 'kajal', Kotak Bank se call kar raha hoon. Meri baat aap se hi ho rahi hai?"
          },
          {
            "speaker": "customer",
            "text": "Haan ji, main Prakash bol raha hoon. Boliye."
          },
          {
            "speaker": "consultant",
            "text": "Sir, main aapki Maruti Swift VXi, 2022 model, ke liye call kiya hai. Gaadi aapke paas hi hai na?"
          },
          {
            "speaker": "customer",
            "text": "Haan ji, mere paas hi hai. Kya baat hai?"
          },
          {
            "speaker": "consultant",
            "text": "Sir, ek special refinance offer hai. Aapki gaadi par abhi loan chal raha hai, right?"
          },
          {
            "speaker": "customer",
            "text": "Haan, chal raha hai. Par mujhe koi aur loan nahi lena. EMI already de raha hoon."
          },
          {
            "speaker": "consultant",
            "text": "Ji sir. Main aapki baat samajhta hoon. Aapko kitni EMI's paid ho chuki hain?"
          },
          {
            "speaker": "customer",
            "text": "10 EMI's. Vaise, aapko kyu jaanna hai?"
          },
          {
            "speaker": "consultant",
            "text": "Sir, yeh isliye zaroori hai kyunki aapko ek bahut bada fayda milne wala hai. Sahi keh raha hoon na?"
          },
          {
            "speaker": "customer",
            "text": "Kaisa fayda?"
          },
          {
            "speaker": "consultant",
            "text": "Sir, ismein aapka purana loan close ho jayega."
          },
          {
            "speaker": "customer",
            "text": "Achaa, aur fir?"
          },
          {
            "speaker": "consultant",
            "text": "Aur baaki paisa seedha aapke account mein aa jayega."
          },
          {
            "speaker": "customer",
            "text": "Kitna paisa?"
          },
          {
            "speaker": "consultant",
            "text": "Aapki gaadi ki market value ka 140% tak. Sahi suna aapne, 140%."
          },
          {
            "speaker": "customer",
            "text": "Itna zyada? Kaise?"
          },
          {
            "speaker": "consultant",
            "text": "Kyunki aapne 10 EMI's de di hain, sir. Ye ek special offer hai. Aapko personal kaam ke liye paisa chahiye tha, right?"
          },
          {
            "speaker": "customer",
            "text": "Haan, par personal loan nahi mil raha."
          },
          {
            "speaker": "consultant",
            "text": "Toh sir, ye offer bilkul aapke liye hi hai. Isse aapki personal funds ki problem solve ho jayegi. Par aapko byaaj rate to zyada lagega, right?"
          },
          {
            "speaker": "customer",
            "text": "Bilkul. Lagta hai byaaj zyada lagega."
          },
          {
            "speaker": "consultant",
            "text": "Par sir, sochiye. Personal loan ka ROI 18-24% hota hai."
          },
          {
            "speaker": "customer",
            "text": "Haan, woh to bahut zyada hai."
          },
          {
            "speaker": "consultant",
            "text": "Yahan aapko ek secured loan mil raha hai sirf 13-16% par. Sahi hai na?"
          },
          {
            "speaker": "customer",
            "text": "Hmm, sahi hai. Toh EMI kya aayegi?"
          },
          {
            "speaker": "consultant",
            "text": "Aapko kitne ka loan chahiye?"
          },
          {
            "speaker": "customer",
            "text": "₹8 lakh ka. Kitni EMI banegi?"
          },
          {
            "speaker": "consultant",
            "text": "Sir, ₹8 lakh ke loan par 5 saal ke liye EMI ₹19,456 hogi. Ye EMI aapke current EMI se bhi kaafi kam ho sakti hai. Aapko theek lag raha hai?"
          },
          {
            "speaker": "customer",
            "text": "Haan, theek hai."
          },
          {
            "speaker": "consultant",
            "text": "Sir, CIBIL score kitna hai aapka?"
          },
          {
            "speaker": "customer",
            "text": "I think it's around 760."
          },
          {
            "speaker": "consultant",
            "text": "Excellent! Sir, aapka case strong hai. Hum 5 din mein aapka loan approve karwa denge. Aapko bas KYC aur bank statement dene honge. Main list WhatsApp kar doon?"
          },
          {
            "speaker": "customer",
            "text": "Theek hai. Bhej dijiye."
          }
        ],
        "analysis": f"'kajal' successfully handles the sales process by increasing the frequency of dialogues. Instead of delivering long monologues, he breaks down his pitch into smaller, bite-sized pieces, asking for the customer's response at each turn. This makes the customer an active participant in the conversation, not just a listener. By asking frequent micro-questions like 'Sahi keh raha hoon na?' or 'Aapko theek lag raha hai?', 'kajal' confirms understanding and builds immediate rapport, making the customer feel heard and understood. This high-frequency approach helps in identifying and overcoming objections in real-time, leading to a smoother and faster close."
      }
    ],
}