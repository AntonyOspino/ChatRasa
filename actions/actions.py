from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet
import psycopg2
from dotenv import load_dotenv
import os

# cargar variables de entorno .env
load_dotenv()
# otener la cadena de conexion
connection_string = os.getenv("NEON_CONNECTION_STRING")

def get_connection():
    return psycopg2.connect(connection_string)


# Usuario
# class ActionValidarUsuarioAPI(Action):
#     def name(self) -> Text:
#         return "action_validar_usuario_api"

#     def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]):
#         nombre_usuario = tracker.get_slot("nombre_usuario")
#         dispatcher.utter_message(text=f"Verificando usuario '{nombre_usuario}' en el sistema... (simulación API)")
#         return []


# Citas
class ActionConsultarCita(Action):
    def name(self):
        return "action_consultar_cita"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: dict):
        conn = None
        cursor = None
        try:
            identificacion = tracker.get_slot("identificacion")

            if not identificacion or not identificacion.isdigit():
                dispatcher.utter_message(text="⚠️ Por favor, ingresa un número de identificación válido (solo dígitos).")
                return []

            conn = get_connection()
            cursor = conn.cursor()

            # Buscar el usuario con esa identificación
            cursor.execute("""
                SELECT id FROM usuario WHERE identificacion = %s;
            """, (identificacion,))
            usuario = cursor.fetchone()

            if not usuario:
                dispatcher.utter_message(text="❌ No encontré ningún usuario con esa identificación.")
                return []

            usuario_id = usuario[0]

            # Buscar citas activas de ese usuario
            cursor.execute("""
                SELECT fecha_cita, hora_cita 
                FROM cita 
                WHERE usuario_paciente_id = %s 
                AND estado_cita = 'activo'
                ORDER BY fecha_cita ASC;
            """, (usuario_id,))

            citas = cursor.fetchall()

            if citas:
                mensajes = []
                for cita in citas:
                    fecha, hora = cita
                    mensajes.append(f"📅 {fecha} a las {hora}")
                if len(citas) == 1:
                    mensaje_final = f"Tienes una cita activa el {citas[0][0]} a las {citas[0][1]} 🩺"
                else:
                    mensaje_final = "Estas son tus citas activas:\n" + "\n".join(mensajes)
                dispatcher.utter_message(text=mensaje_final)
            else:
                dispatcher.utter_message(text="No tienes citas activas registradas 🗓️")
                
        except Exception as e:
            dispatcher.utter_message(text=f"⚠️ Error al consultar la base de datos: {e}")
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

        return []



# Diagnosticos
# class ActionObtenerDiagnosticoAPI(Action):
#     def name(self) -> Text:
#         return "action_obtener_diagnostico_api"

#     def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]):
#         dispatcher.utter_message(text="Buscando tu diagnóstico más reciente... (simulación API)")
#         dispatcher.utter_message(text="Último diagnóstico: presión arterial estable, continuar con dieta saludable.")
#         return []


# Medicos y notificaciones
# class ActionObtenerMedicoAPI(Action):
#     def name(self) -> Text:
#         return "action_obtener_medico_api"

#     def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]):
#         dispatcher.utter_message(text="Buscando Tu Médico... (simulación API)")
#         dispatcher.utter_message(text="Tu Médico Asignado Es: Dr. María López")
#         return []


# Sistomas
# class ActionRecomendarSegunSintomas(Action):
#     def name(self) -> Text:
#         return "action_recomendar_según_sintomas"

#     def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]):
#         sintoma = tracker.latest_message.get("text")
#         sintomas_usuario.append(sintoma)

#         # respuestas personalizadas
#         recomendaciones = {
#             "pecho": "El dolor en el pecho puede ser signo de angina o infarto. Evita esfuerzos y consulta un médico.",
#             "mare": "El mareo puede estar asociado a baja presión o ritmo cardíaco irregular.",
#             "palpit": "Las palpitaciones pueden deberse al estrés o arritmias. Evita cafeína y mantén reposo.",
#             "presión": "Los cambios de presión afectan directamente al sistema cardiovascular. Controla tu tensión arterial.",
#             "falta de aire": "La falta de aire puede indicar insuficiencia cardíaca o ansiedad.",
#             "hinchad": "La hinchazón en pies puede deberse a retención de líquidos o problemas cardíacos."
#         }

#         texto = sintoma.lower()
#         recomendacion = "Te recomiendo mantener reposo y observar tus síntomas."
#         for palabra, respuesta in recomendaciones.items():
#             if palabra in texto:
#                 recomendacion = respuesta
#                 break

#         dispatcher.utter_message(text=f"Gracias por compartirlo. {recomendacion}")
#         return []
