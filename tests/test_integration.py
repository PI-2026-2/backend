"""Exercise patient, record, chat, catalog and game contracts with SQLite."""

import os
import tempfile
import unittest
from pathlib import Path


class IntegrationEndpointsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.previous_directory = os.getcwd()
        cls.temp_directory = tempfile.TemporaryDirectory()
        os.chdir(cls.temp_directory.name)
        Path(".env").write_text(
            "DATABASE_URL=sqlite:///integration-test.sqlite3\nSECRET_KEY=test-only-secret-long-enough-for-hs256\n",
            encoding="utf-8",
        )
        from fastapi.testclient import TestClient
        from sqlmodel import create_engine
        import app.database as database
        from app.main import app
        from app.model.integration import CardProgram, CardResponse, ChatEntry, ClinicalNote, PatientLink
        from app.model.tables import Baralhos, Cartas, Etiquetas, Usuarios

        database.engine = create_engine("sqlite:///integration-test.sqlite3", connect_args={"check_same_thread": False})
        for model in (Usuarios, Etiquetas, Baralhos, Cartas, PatientLink, ClinicalNote, ChatEntry, CardProgram, CardResponse):
            model.__table__.create(database.engine)
        cls.engine = database.engine
        cls.client = TestClient(app)

    @classmethod
    def tearDownClass(cls):
        cls.client.close()
        cls.engine.dispose()
        os.chdir(cls.previous_directory)
        cls.temp_directory.cleanup()

    def register(self, email, role="TERAPEUTA"):
        response = self.client.post("/cadastro", json={
            "nome": email.split("@")[0], "email": email, "senha": "secret123",
            "telefone": "11999999999", "data_nascimento": "1990-05-12",
            "genero": "Feminino", "tipo": role,
        })
        self.assertEqual(response.status_code, 200, response.text)
        token = self.client.post("/login", json={"email": email, "senha": "secret123"}).json()["token"]["access_token"]
        return response.json()["cadastro"]["id"], {"Authorization": f"Bearer {token}"}

    def test_persistent_flows_and_access_control(self):
        from sqlmodel import Session
        from app.model.tables import Baralhos, Cartas, Etiquetas

        therapist_id, therapist = self.register("terapeuta@example.com")
        _, other_therapist = self.register("outro@example.com")
        self_registered = self.client.post("/cadastro", json={
            "nome": "Paciente Vinculado", "email": "vinculado@example.com", "senha": "secret123",
            "telefone": "11977777777", "data_nascimento": "2001-01-01",
            "genero": "Feminino", "tipo": "PACIENTE", "terapeuta_email": "terapeuta@example.com",
        })
        self.assertEqual(self_registered.status_code, 200, self_registered.text)
        payload = {
            "nome": "Paciente Um", "email": "paciente@example.com", "senha": "secret123",
            "telefone": "11988888888", "data_nascimento": "2000-01-01",
            "genero": "Feminino", "tipo": "PACIENTE", "diagnosis": "Ansiedade", "goal": "Autocuidado",
        }
        created = self.client.post("/patients", json=payload, headers=therapist)
        self.assertEqual(created.status_code, 201, created.text)
        patient_id = created.json()["id"]
        self.assertEqual(created.json()["diagnosis"], "Ansiedade")
        self.assertEqual(len(self.client.get("/patients", headers=therapist).json()), 2)
        self.assertEqual(self.client.get(f"/patients/{patient_id}/notes", headers=other_therapist).status_code, 404)
        patient = {"Authorization": "Bearer " + self.client.post(
            "/login", json={"email": payload["email"], "senha": payload["senha"]}
        ).json()["token"]["access_token"]}

        note = self.client.post(f"/patients/{patient_id}/notes", json={"title": "Sessão", "text": "Primeiro encontro"}, headers=therapist)
        self.assertEqual(note.status_code, 201, note.text)
        note_id = note.json()["id"]
        edited = self.client.put(f"/patients/{patient_id}/notes/{note_id}", json={"title": "Sessão 1", "text": "Plano"}, headers=therapist)
        self.assertEqual(edited.status_code, 200, edited.text)
        self.assertEqual(self.client.get(f"/patients/{patient_id}/notes", headers=therapist).json()[0]["text"], "Plano")
        self.assertEqual(self.client.get(f"/patients/{patient_id}/notes", headers=patient).status_code, 403)

        sent = self.client.post("/messages", json={"patient_id": patient_id, "text": "Olá"}, headers=therapist)
        self.assertEqual(sent.status_code, 201, sent.text)
        self.assertEqual(sent.json()["sender"], "therapist")
        reply = self.client.post("/messages", json={"text": "Resposta"}, headers=patient)
        self.assertEqual(reply.status_code, 201, reply.text)
        self.assertEqual(reply.json()["sender"], "patient")
        self.assertEqual(len(self.client.get("/conversations", headers=therapist).json()), 2)
        self.assertEqual(len(self.client.get("/messages", headers=patient).json()), 2)
        self.assertEqual(self.client.get("/messages", params={"patient_id": patient_id}, headers=other_therapist).status_code, 404)

        with Session(self.engine) as session:
            theme = Etiquetas(nome="Ansiedade")
            session.add(theme); session.flush()
            deck = Baralhos(nome="Baralho A", etiqueta_id=theme.id)
            session.add(deck); session.flush()
            cards = [Cartas(frente=f"Assunto {index}", verso=f"Pergunta {index}", ativa=True,
                            criado_por_usuario_id=therapist_id, baralho_id=deck.id) for index in range(7)]
            session.add_all(cards); session.commit()
            card_ids = [card.id for card in cards]

        catalog = self.client.get("/catalog", headers=patient)
        self.assertEqual(catalog.status_code, 200, catalog.text)
        self.assertEqual(len(catalog.json()["cards"]), 7)
        program = self.client.post("/programs", json={"patient_id": patient_id, "card_ids": card_ids}, headers=therapist)
        self.assertEqual(program.status_code, 201, program.text)
        self.assertEqual(len(self.client.get("/programs", headers=patient).json()), 1)
        daily = self.client.post("/responses", json={"card_id": card_ids[0], "mode": "daily", "answer": "Hoje"}, headers=patient)
        self.assertEqual(daily.status_code, 201, daily.text)
        session_response = self.client.post("/responses", json={"patient_id": patient_id, "card_id": card_ids[1], "mode": "session", "answer": "Na sessão"}, headers=therapist)
        self.assertEqual(session_response.status_code, 201, session_response.text)
        self.assertEqual(len(self.client.get("/responses", headers=patient).json()), 2)
        self.assertEqual(self.client.post("/responses", json={"patient_id": patient_id, "card_id": card_ids[1], "mode": "session", "answer": "Não"}, headers=other_therapist).status_code, 404)


if __name__ == "__main__":
    unittest.main()
