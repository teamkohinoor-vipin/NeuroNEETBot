import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
MONGO_URI = os.getenv("MONGO_URI")
ADMIN_ID = int(os.getenv("ADMIN_ID", 0))
SUPPORT_CHANNEL = os.getenv("SUPPORT_CHANNEL", "")
DEVELOPER_USERNAME = os.getenv("DEVELOPER_USERNAME", "")
GROUP_ID = int(os.getenv("GROUP_ID", 0))

TIMEZONE = "Asia/Kolkata"
QUIZ_INTERVAL_MINUTES = 20

SCHEDULE = [
    {"start": 6, "end": 12, "subject": "Physics"},
    {"start": 12, "end": 18, "subject": "Chemistry"},
    {"start": 18, "end": 24, "subject": "Biology"},
]

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
"🔘 Cell Cycle and Cell Division",
"🔘 Transport in Plants",
"🔘 Mineral Nutrition",
"🔘 Photosynthesis in Higher Plants",
"🔘 Respiration in Plants",
"🔘 Plant Growth and Development",
"🔘 Digestion and Absorption",
"🔘 Breathing and Exchange of Gases",
"🔘 Body Fluids and Circulation",
"🔘 Excretory Products and their Elimination",
"🔘 Locomotion and Movement",
"🔘 Neural Control and Coordination",
"🔘 Chemical Coordination and Integration"
],

12: [
"🔘 Reproduction in Organisms",
"🔘 Sexual Reproduction in Flowering Plants",
"🔘 Human Reproduction",
"🔘 Reproductive Health",
"🔘 Principles of Inheritance and Variation",
"🔘 Molecular Basis of Inheritance",
"🔘 Evolution",
"🔘 Human Health and Disease",
"🔘 Strategies for Enhancement in Food Production",
"🔘 Microbes in Human Welfare",
"🔘 Biotechnology: Principles and Processes",
"🔘 Biotechnology and its Applications",
"🔘 Organisms and Populations",
"🔘 Ecosystem",
"🔘 Biodiversity and Conservation",
"🔘 Environmental Issues"
]

}

}
