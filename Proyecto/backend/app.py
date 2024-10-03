from flask import Flask, jsonify, request
from flask_cors import CORS
from elasticsearch import Elasticsearch


app = Flask(__name__)
CORS(app)  # Habilita CORS para todas las rutas

# Configura la conexión a Elasticsearch
es = Elasticsearch([{'host': 'localhost', 'port': 9200, 'scheme': 'http'}])

alerts = []

#Logica general AUNQUE NO SE USE COMPLETA
@app.route('/alert', methods=['POST'])
def receive_alert():
    alert_data = request.json
    alerts.append(alert_data)
    # Almaceno la información del dashboard en la alerta
    dashboard_url = alert_data.get('dashboardURL')  # Suponiendo que 'dashboardURL' viene en la alerta
    alerts.append({
        'alert': alert_data,
        'dashboard_url': dashboard_url
    })
    
    return jsonify({"status": "received"}), 200

@app.route('/alerts/latest', methods=['GET'])
def get_latest_alert():
    # Devolver la alerta más reciente con la información del dashboard
    if alerts:
        return jsonify(alerts[-1])
    return jsonify({"status": "no alerts"}), 200

@app.route('/alerts', methods=['GET'])
def get_alerts():
    return jsonify(alerts)

@app.route('/trigger_alert', methods=['GET'])
def trigger_alert():
    alert_data = {"message": "Alerta simulada", "severity": "medium"}
    alerts.append(alert_data)
    print("Triggered alert:", alert_data)
    return jsonify({"status": "alert triggered"}), 200

@app.route('/usuarios', methods=['GET'])
def get_users():
    indices = es.indices.get_alias(index="user*") 
    user_count = len(indices)
    
    users = [f'Usuario {i + 1}' for i in range(user_count)]
    
    return jsonify(users)

# @app.route('/', methods=['GET'])
# def obtener_actividades_por_usuarios():
#     indices = es.indices.get_alias(index="*")  # Obtiene todos los índices

#     actividades_por_usuario = {}

#     for index in indices:
#         # Consulta al índice del usuario actual
#         query = {
#             "query": {
#                 "match_all": {}
#             }
#         }
#         resultado = es.search(index=index, body=query)

#         # Extraemos los nombres de las actividades sin duplicados
#         actividades = list(set(hit["_source"]["activity"] for hit in resultado["hits"]["hits"]))

#         # Asignamos las actividades al usuario correspondiente (nombre del índice)
#         actividades_por_usuario[index] = actividades

#     return jsonify(actividades_por_usuario)

@app.route('/actividadesUsuario/<usuario_id>', methods=['GET'])
def obtener_actividades_por_usuario(usuario_id):
    if not usuario_id.isdigit() or int(usuario_id) <= 0:
        return jsonify({"error": "Usuario ID no válido"}), 400

    index_name = f"user{usuario_id}"  # Genera el nombre del índice con base en el usuario_id
    
    if not es.indices.exists(index=index_name):
        return jsonify({"error": "El índice del usuario no existe"}), 404

    try:
        query = {
            "query": {
                "match_all": {}
            }
        }
        resultado = es.search(index=index_name, body=query)

        actividades = list(set(hit["_source"]["activity"] for hit in resultado["hits"]["hits"]))

        return jsonify(actividades)
    except Exception as e:
        print(f"Error en el servidor: {e}")
        return jsonify({"error": "Error interno del servidor"}), 500

@app.route('/sensores', methods=['GET'])
def obtener_tipos_sensores():
    try:
        # Consulta para obtener los tipos de sensores únicos
        query = {
            "size": 0,  # No necesitamos devolver los documentos
            "aggs": {
                "tipos_sensores": {
                    "terms": {
                        "field": "sensor_id.keyword",
                        "size": 1000  # Ajusta este valor según la cantidad de tipos de sensores
                    }
                }
            }
        }
        resultado = es.search(index="sensores", body=query)
        tipos_sensores = [bucket["key"] for bucket in resultado["aggregations"]["tipos_sensores"]["buckets"]]

        return jsonify(tipos_sensores)
    except Exception as e:
        print(f"Error en el servidor: {e}")
        return jsonify({"error": "Error interno del servidor"}), 500

if __name__ == '__main__':
    # Permitir conexiones desde cualquier IP de la red local
    app.run(debug=True, host='0.0.0.0')
