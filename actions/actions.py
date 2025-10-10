from typing import Any, Text, Dict, List
from rasa_sdk import Action, Tracker, FormValidationAction
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet, FollowupAction, AllSlotsReset
import requests
import re

class ActionProcessLogin(Action):
    def name(self) -> Text:
        return "action_process_login"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        # Extract username and password from user input
        user_message = tracker.latest_message.get("text", "")
        print(f"🔍 Mensaje recibido: '{user_message}'")
        username_match = re.search(r"(?:usuario:\s*)?([^\s,]+)", user_message, re.IGNORECASE)
        password_match = re.search(r"(?:contraseña:\s*)?([^\s,]+)$", user_message, re.IGNORECASE)


        if not username_match or not password_match:
            print("❌ No se pudo extraer credenciales con regex")

            dispatcher.utter_message(response="utter_login_failed")
            return [
                SlotSet("rol", None),
                SlotSet("username", None),
                SlotSet("identificacion", None),
                SlotSet("nombre", None),
                SlotSet("apellido", None)
            ]

        username = username_match.group(1)
        password = password_match.group(1)

        # Simulate API call to login endpoint
        try:
            response = requests.post(
                "http://localhost:3000/usuario/login",
                json={"username": username, "password": password}
            )
            response.raise_for_status()
            data = response.json()
            print(f"✅ Respuesta de login: {data}")

            if data.get("message") == "Inicio de sesión exitoso":
                user_data = data.get("data", {})
                dispatcher.utter_message(
                    text=f"¡Bienvenido(a), {user_data.get('rol')} {user_data.get('nombre')} {user_data.get('apellido')}! "
                         "Vamos a realizar un diagnóstico. Responde las siguientes preguntas con 'sí' o 'no'."
                )
                events = [
                    SlotSet("username", username),
                    SlotSet("identificacion", user_data.get("identificacion")),
                    SlotSet("nombre", user_data.get("nombre")),
                    SlotSet("apellido", user_data.get("apellido")),
                    SlotSet("rol", user_data.get("rol")),
                    SlotSet("respuestas", []),
                    SlotSet("question_count", 0),
                    SlotSet("answer_1", None),
                    SlotSet("answer_2", None),
                    SlotSet("answer_3", None),
                    SlotSet("answer_4", None),
                    SlotSet("answer_5", None),
                ]
                events.append(FollowupAction(name="diagnosis_form"))
                return events
            else:
                dispatcher.utter_message(response="utter_login_failed")
                return [
                    SlotSet("rol", None),
                    SlotSet("username", None),
                    SlotSet("identificacion", None),
                    SlotSet("nombre", None),
                    SlotSet("apellido", None)
                ]
        except requests.RequestException:
            dispatcher.utter_message(response="utter_login_failed")
            return [
                SlotSet("rol", None),
                SlotSet("username", None),
                SlotSet("identificacion", None),
                SlotSet("nombre", None),
                SlotSet("apellido", None)
            ]

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
    

class ActionSubmitDiagnosis(Action):
    def name(self) -> Text:
        return "action_submit_diagnosis"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        identificacion = tracker.get_slot("identificacion")
        respuestas = tracker.get_slot("respuestas") or []

        payload = {"identificacion": identificacion, "respuestas": respuestas}

        try:
            response = requests.post("http://localhost:3000/respuesta/add", json=payload)
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


class ActionEndSession(Action):
    def name(self) -> Text:
        return "action_end_session"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        # Reset all slots to end the session
        return [
            AllSlotsReset()
        ]