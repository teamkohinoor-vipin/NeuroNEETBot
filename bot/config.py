import os
from dotenv import load_dotenv
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
MONGO_URI = os.getenv("MONGO_URI")
ADMIN_ID = int(os.getenv("ADMIN_ID", 0))
SUPPORT_CHANNEL = os.getenv("SUPPORT_CHANNEL", "")
DEVELOPER_USERNAME = os.getenv("DEVELOPER_USERNAME", "")
GROUP_ID = int(os.getenv("GROUP_ID", 0))

TIMEZONE = "Asia/Kolkata"
QUIZ_INTERVAL_MINUTES = 20

SCHEDULE = ["09:00", "12:00", "15:00", "18:00", "21:00"]

CHAPTERS_PER_PAGE = 5

def chapter_menu(subject, class_no, page=0):

    chapters = CHAPTERS[subject][class_no]

    start = page * CHAPTERS_PER_PAGE
    end = start + CHAPTERS_PER_PAGE

    page_chapters = chapters[start:end]

    buttons = []

    for i, ch in enumerate(page_chapters):

        buttons.append([
            InlineKeyboardButton(
                ch,
                callback_data=f"chapter_{subject}_{class_no}_{start+i}"
            )
        ])

    nav = []

    if page > 0:
        nav.append(
            InlineKeyboardButton(
                "⬅ Back",
                callback_data=f"chap_{subject}_{class_no}_{page-1}"
            )
        )

    if end < len(chapters):
        nav.append(
            InlineKeyboardButton(
                "➡ Next",
                callback_data=f"chap_{subject}_{class_no}_{page+1}"
            )
        )

    if nav:
        buttons.append(nav)

    buttons.append([
        InlineKeyboardButton(
            "🔙 Class Menu",
            callback_data=f"class_{class_no}"
        )
    ])

    return InlineKeyboardMarkup(buttons)


CHAPTERS = {

"Physics": {

11: [
"🔘 Physical World",
"🔘 Units and Measurements",
"🔘 Motion in a Straight Line",
"🔘 Motion in a Plane",
"🔘 Laws of Motion",
"🔘 Work, Energy and Power",
"🔘 System of Particles and Rotational Motion",
"🔘 Gravitation",
"🔘 Mechanical Properties of Solids",
"🔘 Mechanical Properties of Fluids",
"🔘 Thermal Properties of Matter",
"🔘 Thermodynamics",
"🔘 Kinetic Theory",
"🔘 Oscillations",
"🔘 Waves"
],

12: [
"🔘 Electric Charges and Fields",
"🔘 Electrostatic Potential and Capacitance",
"🔘 Current Electricity",
"🔘 Moving Charges and Magnetism",
"🔘 Magnetism and Matter",
"🔘 Electromagnetic Induction",
"🔘 Alternating Current",
"🔘 Electromagnetic Waves",
"🔘 Ray Optics and Optical Instruments",
"🔘 Wave Optics",
"🔘 Dual Nature of Radiation and Matter",
"🔘 Atoms",
"🔘 Nuclei",
"🔘 Semiconductor Electronics"
]

},

"Chemistry": {

11: [
"🔘 Some Basic Concepts of Chemistry",
"🔘 Structure of Atom",
"🔘 Classification of Elements and Periodicity in Properties",
"🔘 Chemical Bonding and Molecular Structure",
"🔘 States of Matter",
"🔘 Thermodynamics",
"🔘 Equilibrium",
"🔘 Redox Reactions",
"🔘 Hydrogen",
"🔘 s-Block Elements",
"🔘 p-Block Elements (Group 13 & 14)",
"🔘 Organic Chemistry – Some Basic Principles and Techniques",
"🔘 Hydrocarbons",
"🔘 Environmental Chemistry"
],

12: [
"🔘 Solid State",
"🔘 Solutions",
"🔘 Electrochemistry",
"🔘 Chemical Kinetics",
"🔘 Surface Chemistry",
"🔘 p-Block Elements",
"🔘 d- and f-Block Elements",
"🔘 Coordination Compounds",
"🔘 Haloalkanes and Haloarenes",
"🔘 Alcohols, Phenols and Ethers",
"🔘 Aldehydes, Ketones and Carboxylic Acids",
"🔘 Amines",
"🔘 Biomolecules",
"🔘 Polymers",
"🔘 Chemistry in Everyday Life"
]

},

"Biology": {

11: [
"🔘 The Living World",
"🔘 Biological Classification",
"🔘 Plant Kingdom",
"🔘 Animal Kingdom",
"🔘 Morphology of Flowering Plants",
"🔘 Anatomy of Flowering Plants",
"🔘 Structural Organisation in Animals",
"🔘 Cell: The Unit of Life",
"🔘 Biomolecules",
"🔘 Cell Cycle and Cell Division"
],

12: [
"🔘 Reproduction in Organisms",
"🔘 Sexual Reproduction in Flowering Plants",
"🔘 Human Reproduction",
"🔘 Reproductive Health",
"🔘 Principles of Inheritance and Variation"
]

}

}
