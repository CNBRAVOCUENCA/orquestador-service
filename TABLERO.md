# 📋 Tablero del proyecto — El Destripador de PDFs

Tablero centralizado de todas las fases y tareas del sistema de microservicios.
Cada fila enlaza a la issue real en su repositorio.

**Estado general:** 68 de 81 tareas completadas.

## Resumen por microservicio

| Microservicio | Repositorio | Tareas | Completadas |
|---|---|---:|---:|
| 📄 Documentos | [documentos-service](https://github.com/CNBRAVOCUENCA/documentos-service) | 15 | 12 |
| 🔍 Extracción | [extraccion-service](https://github.com/CNBRAVOCUENCA/extraccion-service) | 22 | 18 |
| 🤖 Resumen (IA) | [resumen-service](https://github.com/CNBRAVOCUENCA/resumen-service) | 7 | 6 |
| 🔔 Notificaciones | [notificaciones-service](https://github.com/CNBRAVOCUENCA/notificaciones-service) | 8 | 7 |
| 🎭 Orquestador | [orquestador-service](https://github.com/CNBRAVOCUENCA/orquestador-service) | 29 | 25 |


## 📄 Documentos — [documentos-service](https://github.com/CNBRAVOCUENCA/documentos-service/issues)

| # | Tarea | Tipo | Estado |
|---:|---|---|---|
| [#3](https://github.com/CNBRAVOCUENCA/documentos-service/issues/3) | **[Roadmap] Plan de migración a microservicios: Documentos → Extracción → Resumen IA → Notificaciones** | 🎯 Fase | 🟢 Abierto |
| [#7](https://github.com/CNBRAVOCUENCA/documentos-service/issues/7) | **[Fase] Microservicio de Documentos** | 🎯 Fase | 🟢 Abierto |
| [#14](https://github.com/CNBRAVOCUENCA/documentos-service/issues/14) | **[Fase] Corrección de bugs encontrados en integración real** | 🎯 Fase | 🟢 Abierto |
| [#1](https://github.com/CNBRAVOCUENCA/documentos-service/issues/1) | Se comienza con microservicio documentos | Tarea | ✅ Completado |
| [#2](https://github.com/CNBRAVOCUENCA/documentos-service/issues/2) | [Documentos] Estructura base del microservicio + modelos y repositorio (TDD) | Tarea | ✅ Completado |
| [#4](https://github.com/CNBRAVOCUENCA/documentos-service/issues/4) | [QA] Prueba de integración end-to-end del ciclo de vida completo del documento | Tarea | ✅ Completado |
| [#5](https://github.com/CNBRAVOCUENCA/documentos-service/issues/5) | Traefik | Tarea | ✅ Completado |
| [#6](https://github.com/CNBRAVOCUENCA/documentos-service/issues/6) | impiar dependencias no utilizadas | Tarea | ✅ Completado |
| [#8](https://github.com/CNBRAVOCUENCA/documentos-service/issues/8) | Estructura en capas + modelo Document | Tarea | ✅ Completado |
| [#9](https://github.com/CNBRAVOCUENCA/documentos-service/issues/9) | DocumentRepository (acceso a MongoDB) | Tarea | ✅ Completado |
| [#10](https://github.com/CNBRAVOCUENCA/documentos-service/issues/10) | DocumentService + validadores + excepciones de dominio | Tarea | ✅ Completado |
| [#11](https://github.com/CNBRAVOCUENCA/documentos-service/issues/11) | Endpoints REST + descarga de binario | Tarea | ✅ Completado |
| [#12](https://github.com/CNBRAVOCUENCA/documentos-service/issues/12) | Suite de tests (TDD) + prueba de integración end-to-end | Tarea | ✅ Completado |
| [#13](https://github.com/CNBRAVOCUENCA/documentos-service/issues/13) | Dockerfile + Traefik + configuración con UV | Tarea | ✅ Completado |
| [#15](https://github.com/CNBRAVOCUENCA/documentos-service/issues/15) | fix: binario del PDF se corrompía al leerlo de MongoDB (bson.Binary) | Tarea | ✅ Completado |


## 🔍 Extracción — [extraccion-service](https://github.com/CNBRAVOCUENCA/extraccion-service/issues)

| # | Tarea | Tipo | Estado |
|---:|---|---|---|
| [#14](https://github.com/CNBRAVOCUENCA/extraccion-service/issues/14) | **[Fase] Microservicio de Extracción de texto** | 🎯 Fase | 🟢 Abierto |
| [#21](https://github.com/CNBRAVOCUENCA/extraccion-service/issues/21) | **[Fase] Corrección de incompatibilidad de formato entre servicios** | 🎯 Fase | 🟢 Abierto |
| [#1](https://github.com/CNBRAVOCUENCA/extraccion-service/issues/1) | [extraccion-service] Microservicio de extracción de texto (TDD) | Tarea | ✅ Completado |
| [#2](https://github.com/CNBRAVOCUENCA/extraccion-service/issues/2) | utilización de UV | Tarea | 🟢 Abierto |
| [#3](https://github.com/CNBRAVOCUENCA/extraccion-service/issues/3) | Fase completada - Extracción de texto PDF | Tarea | 🟢 Abierto |
| [#4](https://github.com/CNBRAVOCUENCA/extraccion-service/issues/4) | Recibir PDF en Base64 desde documentos-service | Tarea | ✅ Completado |
| [#5](https://github.com/CNBRAVOCUENCA/extraccion-service/issues/5) | Decodificar Base64 a bytes | Tarea | ✅ Completado |
| [#6](https://github.com/CNBRAVOCUENCA/extraccion-service/issues/6) | Extraer y concatenar texto con pypdf | Tarea | ✅ Completado |
| [#7](https://github.com/CNBRAVOCUENCA/extraccion-service/issues/7) | Definir DTOs Pydantic | Tarea | ✅ Completado |
| [#8](https://github.com/CNBRAVOCUENCA/extraccion-service/issues/8) | Manejar PDF protegido con contraseña | Tarea | ✅ Completado |
| [#9](https://github.com/CNBRAVOCUENCA/extraccion-service/issues/9) | Manejar PDF corrupto o inválido | Tarea | ✅ Completado |
| [#10](https://github.com/CNBRAVOCUENCA/extraccion-service/issues/10) | Agregar health check | Tarea | ✅ Completado |
| [#11](https://github.com/CNBRAVOCUENCA/extraccion-service/issues/11) | Agregar pruebas unitarias e integración | Tarea | ✅ Completado |
| [#12](https://github.com/CNBRAVOCUENCA/extraccion-service/issues/12) | Configurar dependencias con uv | Tarea | ✅ Completado |
| [#13](https://github.com/CNBRAVOCUENCA/extraccion-service/issues/13) | Publicar cambios en main | Tarea | ✅ Completado |
| [#15](https://github.com/CNBRAVOCUENCA/extraccion-service/issues/15) | PdfTextExtractor (extracción con pypdf) | Tarea | ✅ Completado |
| [#16](https://github.com/CNBRAVOCUENCA/extraccion-service/issues/16) | DocumentosClient (cliente HTTP) | Tarea | ✅ Completado |
| [#17](https://github.com/CNBRAVOCUENCA/extraccion-service/issues/17) | ExtractionService (orquestación) | Tarea | ✅ Completado |
| [#18](https://github.com/CNBRAVOCUENCA/extraccion-service/issues/18) | Endpoint POST /extract + exception handlers | Tarea | ✅ Completado |
| [#19](https://github.com/CNBRAVOCUENCA/extraccion-service/issues/19) | Suite de tests (TDD, 11 tests) | Tarea | ✅ Completado |
| [#20](https://github.com/CNBRAVOCUENCA/extraccion-service/issues/20) | Dockerfile + configuración con UV | Tarea | ✅ Completado |
| [#22](https://github.com/CNBRAVOCUENCA/extraccion-service/issues/22) | fix: leer el PDF como bytes crudos (revertir Base64 incompatible) | Tarea | ✅ Completado |


## 🤖 Resumen (IA) — [resumen-service](https://github.com/CNBRAVOCUENCA/resumen-service/issues)

| # | Tarea | Tipo | Estado |
|---:|---|---|---|
| [#2](https://github.com/CNBRAVOCUENCA/resumen-service/issues/2) | **[Fase] Microservicio de Resumen con IA** | 🎯 Fase | 🟢 Abierto |
| [#1](https://github.com/CNBRAVOCUENCA/resumen-service/issues/1) | [resumen-service] Microservicio de resumen con IA / Gemini (TDD) | Tarea | ✅ Completado |
| [#3](https://github.com/CNBRAVOCUENCA/resumen-service/issues/3) | LLMClient (interfaz) + GeminiClient (impl. real) | Tarea | ✅ Completado |
| [#4](https://github.com/CNBRAVOCUENCA/resumen-service/issues/4) | ResumenService (prompt + validación) | Tarea | ✅ Completado |
| [#5](https://github.com/CNBRAVOCUENCA/resumen-service/issues/5) | Endpoint POST /summarize + exception handlers | Tarea | ✅ Completado |
| [#6](https://github.com/CNBRAVOCUENCA/resumen-service/issues/6) | Suite de tests (TDD, 9 tests) | Tarea | ✅ Completado |
| [#7](https://github.com/CNBRAVOCUENCA/resumen-service/issues/7) | Dockerfile + configuración con UV | Tarea | ✅ Completado |


## 🔔 Notificaciones — [notificaciones-service](https://github.com/CNBRAVOCUENCA/notificaciones-service/issues)

| # | Tarea | Tipo | Estado |
|---:|---|---|---|
| [#2](https://github.com/CNBRAVOCUENCA/notificaciones-service/issues/2) | **[Fase] Microservicio de Notificaciones / Estado** | 🎯 Fase | 🟢 Abierto |
| [#1](https://github.com/CNBRAVOCUENCA/notificaciones-service/issues/1) | [notificaciones-service] Microservicio de estado/notificaciones (TDD) | Tarea | ✅ Completado |
| [#3](https://github.com/CNBRAVOCUENCA/notificaciones-service/issues/3) | Modelo EstadoDocumento + estados válidos | Tarea | ✅ Completado |
| [#4](https://github.com/CNBRAVOCUENCA/notificaciones-service/issues/4) | EstadoRepository (upsert en MongoDB) | Tarea | ✅ Completado |
| [#5](https://github.com/CNBRAVOCUENCA/notificaciones-service/issues/5) | EstadoService (transiciones + historial) | Tarea | ✅ Completado |
| [#6](https://github.com/CNBRAVOCUENCA/notificaciones-service/issues/6) | Endpoints REST (registrar/consultar/listar) | Tarea | ✅ Completado |
| [#7](https://github.com/CNBRAVOCUENCA/notificaciones-service/issues/7) | Suite de tests (TDD, 9 tests) | Tarea | ✅ Completado |
| [#8](https://github.com/CNBRAVOCUENCA/notificaciones-service/issues/8) | Dockerfile + configuración con UV | Tarea | ✅ Completado |


## 🎭 Orquestador — [orquestador-service](https://github.com/CNBRAVOCUENCA/orquestador-service/issues)

| # | Tarea | Tipo | Estado |
|---:|---|---|---|
| [#1](https://github.com/CNBRAVOCUENCA/orquestador-service/issues/1) | **[Fase] Orquestación y Saga del sistema** | 🎯 Fase | 🟢 Abierto |
| [#8](https://github.com/CNBRAVOCUENCA/orquestador-service/issues/8) | **[Fase] Front-end y prueba end-to-end del sistema** | 🎯 Fase | 🟢 Abierto |
| [#17](https://github.com/CNBRAVOCUENCA/orquestador-service/issues/17) | **[Fase] Puesta en marcha del sistema completo y resolución de bugs de integración** | 🎯 Fase | 🟢 Abierto |
| [#24](https://github.com/CNBRAVOCUENCA/orquestador-service/issues/24) | **[Fase] Mejoras de cumplimiento 12-Factor App y SOLID** | 🎯 Fase | 🟢 Abierto |
| [#2](https://github.com/CNBRAVOCUENCA/orquestador-service/issues/2) | Implementar SagaService (flujo + compensación) | Tarea | ✅ Completado |
| [#3](https://github.com/CNBRAVOCUENCA/orquestador-service/issues/3) | Cliente HTTP hacia los microservicios (MicroserviciosClient) | Tarea | ✅ Completado |
| [#4](https://github.com/CNBRAVOCUENCA/orquestador-service/issues/4) | Integrar Redis como cache de resultados | Tarea | ✅ Completado |
| [#5](https://github.com/CNBRAVOCUENCA/orquestador-service/issues/5) | docker-compose + Traefik (gateway) | Tarea | ✅ Completado |
| [#6](https://github.com/CNBRAVOCUENCA/orquestador-service/issues/6) | Load testing con Vegeta | Tarea | ✅ Completado |
| [#7](https://github.com/CNBRAVOCUENCA/orquestador-service/issues/7) | Configuración con UV (uv.lock) | Tarea | ✅ Completado |
| [#9](https://github.com/CNBRAVOCUENCA/orquestador-service/issues/9) | feat: página web para subir PDF y ver la orquestación en vivo | Tarea | ✅ Completado |
| [#10](https://github.com/CNBRAVOCUENCA/orquestador-service/issues/10) | feat: endpoint /procesar-completo (subir + Saga en un paso) | Tarea | ✅ Completado |
| [#11](https://github.com/CNBRAVOCUENCA/orquestador-service/issues/11) | feat: CORS para permitir llamadas desde el navegador | Tarea | ✅ Completado |
| [#12](https://github.com/CNBRAVOCUENCA/orquestador-service/issues/12) | feat: MicroserviciosClient.subir_documento + documentos_url | Tarea | ✅ Completado |
| [#13](https://github.com/CNBRAVOCUENCA/orquestador-service/issues/13) | fix: agregar python-multipart a dependencias | Tarea | ✅ Completado |
| [#14](https://github.com/CNBRAVOCUENCA/orquestador-service/issues/14) | docs: guía + docker-compose para levantar todo con Docker | Tarea | ✅ Completado |
| [#15](https://github.com/CNBRAVOCUENCA/orquestador-service/issues/15) | fix: mongomock faltante al instalar en modo local | Tarea | ✅ Completado |
| [#16](https://github.com/CNBRAVOCUENCA/orquestador-service/issues/16) | test: verificación end-to-end (los 5 servicios se comunican) | Tarea | ✅ Completado |
| [#18](https://github.com/CNBRAVOCUENCA/orquestador-service/issues/18) | fix: el binario del PDF se corrompía al leerlo de MongoDB (bson.Binary → bytes) | Tarea | ✅ Completado |
| [#19](https://github.com/CNBRAVOCUENCA/orquestador-service/issues/19) | fix: incompatibilidad de formato entre emisor y receptor (Base64 vs bytes crudos) | Tarea | ✅ Completado |
| [#20](https://github.com/CNBRAVOCUENCA/orquestador-service/issues/20) | fix: el orquestador no conocía la URL de documentos (falta DOCUMENTOS_URL) | Tarea | ✅ Completado |
| [#21](https://github.com/CNBRAVOCUENCA/orquestador-service/issues/21) | fix: Docker construía código viejo (SERVICE_REF clavado a commits desactualizados) | Tarea | ✅ Completado |
| [#22](https://github.com/CNBRAVOCUENCA/orquestador-service/issues/22) | fix: actualizar modelo de IA (Google dio de baja gemini-1.5-flash y gemini-2.5) | Tarea | ✅ Completado |
| [#23](https://github.com/CNBRAVOCUENCA/orquestador-service/issues/23) | docs: front-end web + docker-compose + guía para levantar el sistema completo | Tarea | ✅ Completado |
| [#25](https://github.com/CNBRAVOCUENCA/orquestador-service/issues/25) | feat: config completa por entorno (.env.example en los 5 servicios) | Tarea | ✅ Completado |
| [#26](https://github.com/CNBRAVOCUENCA/orquestador-service/issues/26) | feat: logs estructurados a stdout (App/logging_config.py) | Tarea | ✅ Completado |
| [#27](https://github.com/CNBRAVOCUENCA/orquestador-service/issues/27) | feat: proceso de administración (scripts/verificar_sistema.py) | Tarea | ✅ Completado |
| [#28](https://github.com/CNBRAVOCUENCA/orquestador-service/issues/28) | docs: build/release/run y paridad dev/prod (DEPLOYMENT.md) | Tarea | ✅ Completado |
| [#29](https://github.com/CNBRAVOCUENCA/orquestador-service/issues/29) | test: demostrar SOLID Abierto/Cerrado (test_open_closed.py) | Tarea | ✅ Completado |


---
*Tablero generado automáticamente a partir de las issues de los 5 repositorios.*