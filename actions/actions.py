from typing import Any, Text, Dict, List
from rasa_sdk import Action, Tracker, FormValidationAction
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet, FollowupAction, AllSlotsReset, ActiveLoop
import requests
import re

BASE_URL = "https://apisistemaexperto.vercel.app"

# Acción para procesar el login del usuario

class ActionProcessLogin(Action):
    def name(self) -> Text:
        return "action_process_login"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        # Extraer credenciales desde los slots
        username = tracker.get_slot("username")
        password = tracker.get_slot("password")
        
        print(f"🔍 Intentando login con usuario: '{username}' y contraseña: '{password}'")

        if not username or not password:
            print("❌ Faltan credenciales en los slots.")
            dispatcher.utter_message(text="No entendí tu usuario o contraseña. Por favor, dímelos de nuevo.")
            return [SlotSet("username", None), SlotSet("password", None)]

        try:
            # Llamada a tu API de login
            response = requests.post(
                f"{BASE_URL}/usuario/login",
                json={"username": username, "password": password}
            )
            response.raise_for_status()
            data = response.json()
            print(f"✅ Respuesta de la API de login: {data}")

            if data.get("message") == "Inicio de sesión exitoso":
                user_data = data.get("data", {})
                
                # Preparamos los slots para el formulario y activamos el form
                return [
                    SlotSet("identificacion", user_data.get("identificacion")),
                    SlotSet("nombre", user_data.get("nombre")),
                    SlotSet("apellido", user_data.get("apellido")),
                    SlotSet("rol", user_data.get("rol")),
                    SlotSet("respuestas", []),
                ]
            else:
                dispatcher.utter_message(response="utter_login_failed")
                return [SlotSet("username", None), SlotSet("password", None)]

        except requests.RequestException as e:
            print(f"❌ Error en la API: {e}")
            dispatcher.utter_message(text="Hubo un problema de conexión al intentar iniciar sesión. Inténtalo más tarde.")
            return [SlotSet("username", None), SlotSet("password", None)]
        
# Validación del formulario de diagnóstico

class ValidateDiagnosisForm(FormValidationAction):
    def name(self) -> Text:
        return "validate_diagnosis_form"

    async def required_slots(
        self,
        slots_mapped_in_domain: List[Text],
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Text]:
        return ["answer_1", "answer_2", "answer_3", "answer_4", "answer_5"]

    async def validate_answer_1(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> Dict[Text, Any]:
        respuestas = tracker.get_slot("respuestas") or []
        respuestas.append({"id_pregunta": 1, "respuesta_valor": slot_value})
        return {"answer_1": slot_value, "respuestas": respuestas}

    async def validate_answer_2(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> Dict[Text, Any]:
        respuestas = tracker.get_slot("respuestas") or []
        respuestas.append({"id_pregunta": 2, "respuesta_valor": slot_value})
        return {"answer_2": slot_value, "respuestas": respuestas}

    async def validate_answer_3(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> Dict[Text, Any]:
        respuestas = tracker.get_slot("respuestas") or []
        respuestas.append({"id_pregunta": 3, "respuesta_valor": slot_value})
        return {"answer_3": slot_value, "respuestas": respuestas}

    async def validate_answer_4(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> Dict[Text, Any]:
        respuestas = tracker.get_slot("respuestas") or []
        respuestas.append({"id_pregunta": 4, "respuesta_valor": slot_value})
        return {"answer_4": slot_value, "respuestas": respuestas}

    async def validate_answer_5(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> Dict[Text, Any]:
        respuestas = tracker.get_slot("respuestas") or []
        respuestas.append({"id_pregunta": 5, "respuesta_valor": slot_value})
        return {"answer_5": slot_value, "respuestas": respuestas}

# Acción para enviar las respuestas y obtener el diagnóstico    

class ActionSubmitDiagnosis(Action):
    def name(self) -> Text:
        return "action_submit_diagnosis"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        identificacion = tracker.get_slot("identificacion")
        respuestas = tracker.get_slot("respuestas") or []

        payload = {"identificacion": identificacion, "respuestas": respuestas}

        try:
            response = requests.post(f"{BASE_URL}/respuesta/add", json=payload)
            response.raise_for_status()
            data = response.json()

            if data.get("message") == "Consulta y diagnóstico procesados exitosamente.":
                diagnostico = data.get("diagnostico", {})

                return [
                    SlotSet("diagnostico_nombre", diagnostico.get("nombre")),
                    SlotSet("diagnostico_descripcion", diagnostico.get("descripcion")),
                    SlotSet("diagnostico_recomendaciones", diagnostico.get("recomendaciones")),
                    SlotSet("diagnostico_nivel_gravedad", diagnostico.get("nivel_gravedad")),
                ]

            else:
                dispatcher.utter_message(response="utter_diagnosis_failed")
                return []

        except requests.RequestException as e:
            print(f"❌ Error en la solicitud del diagnóstico: {e}")
            dispatcher.utter_message(response="utter_diagnosis_failed")
            return []

# Acción para finalizar la sesión

class ActionEndSession(Action):
    def name(self) -> Text:
        return "action_end_session"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        # Reset all slots to end the session
        return [
            AllSlotsReset()
        ]