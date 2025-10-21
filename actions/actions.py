from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from typing import Any, Text, Dict, List
import datetime

# simulación de BD en memoria
sintomas_usuario = []

# Usuario
class ActionValidarUsuarioAPI(Action):
    def name(self) -> Text:
        return "action_validar_usuario_api"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]):
        nombre_usuario = tracker.get_slot("nombre_usuario")
        dispatcher.utter_message(text=f"Verificando usuario '{nombre_usuario}' en el sistema... (simulación API)")
        return []
class ActionGuardarEstadoAnimoAPI(Action):
    def name(self) -> Text:
        return "action_guardar_estado_animo_api"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]):
        estado_animo = tracker.latest_message.get("text")
        dispatcher.utter_message(text=f"Guardando estado de ánimo '{estado_animo}' en la base de datos (simulación API)...")
        return []


# Citas
class ActionAgendarCitaAPI(Action):
    def name(self) -> Text:
        return "action_agendar_cita_api"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]):
        dispatcher.utter_message(text="Creando cita médica... (simulación API)")
        dispatcher.utter_message(text="✅ Tu cita fue registrada correctamente. Te notificaremos la fecha y el médico asignado.")
        return []
class ActionCancelarCitaAPI(Action):
    def name(self) -> Text:
        return "action_cancelar_cita_api"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]):
        dispatcher.utter_message(text="Cancelando cita médica... (simulación API)")
        dispatcher.utter_message(text="✅ Cita cancelada correctamente.")
        return []
class ActionObtenerCitasAPI(Action):
    def name(self) -> Text:
        return "action_obtener_citas_api"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]):
        dispatcher.utter_message(text="Buscando tus citas médicas... (simulación API)")
        dispatcher.utter_message(text="📅 Tienes 2 citas programadas:")
        dispatcher.utter_message(text="1️⃣ 15 de mayo a las 10:00")
        dispatcher.utter_message(text="2️⃣ 20 de mayo a las 14:00")
        return []



# Diagnosticos
class ActionGuardarDiagnosticoAPI(Action):
    def name(self) -> Text:
        return "action_guardar_diagnostico_api"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]):
        diagnostico = tracker.latest_message.get("text")
        dispatcher.utter_message(text=f"Guardando diagnóstico '{diagnostico}' en la base de datos (simulación API)...")
        return []
class ActionObtenerDiagnosticoAPI(Action):
    def name(self) -> Text:
        return "action_obtener_diagnostico_api"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]):
        dispatcher.utter_message(text="Buscando tu diagnóstico más reciente... (simulación API)")
        dispatcher.utter_message(text="Último diagnóstico: presión arterial estable, continuar con dieta saludable.")
        return []


# Medicos y notificaciones
class ActionObtenerMedicoAPI(Action):
    def name(self) -> Text:
        return "action_obtener_medico_api"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]):
        dispatcher.utter_message(text="Buscando Tu Médico... (simulación API)")
        dispatcher.utter_message(text="Tu Médico Asignado Es: Dr. María López")
        return []
class ActionEnviarNotificacionAPI(Action):
    def name(self) -> Text:
        return "action_enviar_notificacion_api"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]):
        dispatcher.utter_message(text="Enviando notificación al médico... (simulación API)")
        dispatcher.utter_message(text="✅ Notificación enviada correctamente.")
        return []


# Sistomas
class ActionGuardarSintomasApi(Action):
    def name(self) -> Text:
        return "action_guardar_sintomas_api"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]):
        global sintomas_usuario

        if not sintomas_usuario:
            dispatcher.utter_message(text="No tengo síntomas registrados para guardar.")
            return []

        diagnostico = ", ".join(sintomas_usuario)
        recomendaciones = "Mantén hábitos saludables y consulta un médico si los síntomas persisten."
        sistemas = "Sistema cardiovascular"
        fecha_creacion = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # simulación de envío a API / base de datos
        print({
            "cita_id": None,
            "diagnostico": diagnostico,
            "recomendaciones": recomendaciones,
            "sistemas": sistemas,
            "fecha_creacion": fecha_creacion
        })

        dispatcher.utter_message(text="✅ Tus síntomas fueron registrados correctamente (simulación API).")
        sintomas_usuario = []
        return []

class ActionRecomendarSegunSintomas(Action):
    def name(self) -> Text:
        return "action_recomendar_según_sintomas"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]):
        sintoma = tracker.latest_message.get("text")
        sintomas_usuario.append(sintoma)

        # respuestas personalizadas
        recomendaciones = {
            "pecho": "El dolor en el pecho puede ser signo de angina o infarto. Evita esfuerzos y consulta un médico.",
            "mare": "El mareo puede estar asociado a baja presión o ritmo cardíaco irregular.",
            "palpit": "Las palpitaciones pueden deberse al estrés o arritmias. Evita cafeína y mantén reposo.",
            "presión": "Los cambios de presión afectan directamente al sistema cardiovascular. Controla tu tensión arterial.",
            "falta de aire": "La falta de aire puede indicar insuficiencia cardíaca o ansiedad.",
            "hinchad": "La hinchazón en pies puede deberse a retención de líquidos o problemas cardíacos."
        }

        texto = sintoma.lower()
        recomendacion = "Te recomiendo mantener reposo y observar tus síntomas."
        for palabra, respuesta in recomendaciones.items():
            if palabra in texto:
                recomendacion = respuesta
                break

        dispatcher.utter_message(text=f"Gracias por compartirlo. {recomendacion}")
        return []
