"""Exercise the public authentication contract with an isolated SQLite users table."""

import os
import tempfile
import unittest

from pathlib import Path


class AuthEndpointsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.previous_directory = os.getcwd()
        cls.temp_directory = tempfile.TemporaryDirectory()
        os.chdir(cls.temp_directory.name)
        Path(".env").write_text(
            "DATABASE_URL=sqlite:///auth-test.sqlite3\nSECRET_KEY=test-only-secret-long-enough-for-hs256\n",
            encoding="utf-8",
        )
        try:
            from fastapi.testclient import TestClient
            from app.database import engine
            from app.main import app
            from app.model.tables import Usuarios

            engine.echo = False
            Usuarios.__table__.create(engine)
            cls.client = TestClient(app)
        except Exception:
            os.chdir(cls.previous_directory)
            cls.temp_directory.cleanup()
            raise

    @classmethod
    def tearDownClass(cls):
        cls.client.close()
        from app.database import engine
        engine.dispose()
        os.chdir(cls.previous_directory)
        cls.temp_directory.cleanup()

    def test_register_login_and_duplicate_email(self):
        payload = {
            "nome": "Ana Lima",
            "email": "ana@example.com",
            "senha": "secret123",
            "telefone": "11999999999",
            "data_nascimento": "1990-05-12",
            "genero": "Feminino",
            "tipo": "TERAPEUTA",
        }
        created = self.client.post("/cadastro", json=payload)
        self.assertEqual(created.status_code, 200, created.text)
        self.assertEqual(created.json()["cadastro"]["tipo"], "TERAPEUTA")
        self.assertNotIn("senha_hash", created.text)

        login = self.client.post("/login", json={"email": payload["email"], "senha": payload["senha"]})
        self.assertEqual(login.status_code, 200, login.text)
        self.assertEqual(login.json()["usuario"]["id"], created.json()["cadastro"]["id"])
        self.assertEqual(login.json()["usuario"]["tipo_usuario"], "TERAPEUTA")
        self.assertTrue(login.json()["token"]["access_token"])

        patient_payload = {**payload, "email": "paciente@example.com", "tipo": "PACIENTE"}
        patient = self.client.post("/cadastro", json=patient_payload)
        self.assertEqual(patient.status_code, 200, patient.text)
        patient_login = self.client.post("/login", json={"email": patient_payload["email"], "senha": payload["senha"]})
        self.assertEqual(patient_login.json()["usuario"]["tipo_usuario"], "PACIENTE")

        self.assertEqual(self.client.post("/cadastro", json=payload).status_code, 409)
        self.assertEqual(self.client.post("/login", json={"email": payload["email"], "senha": "wrong"}).status_code, 401)
        self.assertEqual(self.client.post("/login", json={"email": "missing@example.com", "senha": "wrong"}).status_code, 401)


if __name__ == "__main__":
    unittest.main()
