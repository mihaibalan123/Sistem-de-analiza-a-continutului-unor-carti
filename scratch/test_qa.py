import os
import sys
import django

# Setup Django environment
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mds_backend.settings')
django.setup()

from analyzer.agents import CharacterQAAgent, DialogAgent

print("Successfully imported Q&A Agent!")

# Set up sample context details
carte_titlu = "Ion"
carte_autor = "Liviu Rebreanu"
personaje_info = (
    "- Ion (Gen: Masculin, Rol: Principal)\n"
    "- Ana (Gen: Feminin, Rol: Principal)\n"
    "- Gheorghe (Gen: Masculin, Rol: Secundar)"
)
relatii_info = (
    "- Ion <-> Ana: 45 dialoguri\n"
    "- Ion <-> Gheorghe: 18 dialoguri\n"
    "- Ana <-> Gheorghe: 5 dialoguri"
)

# Test CharacterQAAgent
dialog_agent = DialogAgent()
qa_agent = CharacterQAAgent(dialog_agent=dialog_agent)

question = "Cine este Ana și ce relație are cu Ion?"
print(f"Asking: '{question}'...")
response = qa_agent.raspunde_intrebare(carte_titlu, carte_autor, personaje_info, relatii_info, question)
print("\n--- RESPONSE FROM AGENT ---")
print(response)
print("---------------------------\n")

print("Q&A Integration Test Completed Successfully!")
