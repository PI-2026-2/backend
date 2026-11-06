import csv
from dataclasses import dataclass
from pathlib import Path

from sqlmodel import Session, select

from app.model.tables import Baralhos, Cartas, Etiquetas, Usuarios

COLUNAS_OBRIGATORIAS = (
    "collection_name",
    "deck_name",
    "subtheme",
    "question",
    "active",
)

VALORES_VERDADEIROS = {"true", "1", "sim", "verdadeiro"}
VALORES_FALSOS = {"false", "0", "nao", "não", "falso"}


@dataclass
class ResultadoImportacao:
    etiquetas_criadas: int = 0
    baralhos_criados: int = 0
    cartas_criadas: int = 0
    cartas_ignoradas: int = 0


class CartaService:
    def importar_csv(
        self,
        session: Session,
        caminho: str | Path,
        criado_por_usuario_id: int,
    ) -> ResultadoImportacao:
        """
        Importa cartas de um CSV.

        collection_name -> Etiquetas.nome
        deck_name       -> Baralhos.nome
        subtheme        -> Cartas.frente
        question        -> Cartas.verso
        active          -> Cartas.ativa

        Tudo ou nada: se qualquer linha for inválida, nada é gravado.
        Reimportar o mesmo arquivo não duplica cartas.
        """
        if session.get(Usuarios, criado_por_usuario_id) is None:
            raise ValueError(f"Usuário {criado_por_usuario_id} não existe.")

        linhas = self._ler_csv(Path(caminho))
        resultado = ResultadoImportacao()

        etiquetas = {e.nome: e for e in session.exec(select(Etiquetas)).all()}
        baralhos = {b.nome: b for b in session.exec(select(Baralhos)).all()}
        existentes = {
            (baralho_id, frente, verso)
            for baralho_id, frente, verso in session.exec(
                select(Cartas.baralho_id, Cartas.frente, Cartas.verso)
            ).all()
        }

        try:
            for linha in linhas:
                etiqueta = etiquetas.get(linha["collection_name"])
                if etiqueta is None:
                    etiqueta = Etiquetas(nome=linha["collection_name"])
                    session.add(etiqueta)
                    session.flush()
                    etiquetas[etiqueta.nome] = etiqueta
                    resultado.etiquetas_criadas += 1

                baralho = baralhos.get(linha["deck_name"])
                if baralho is None:
                    baralho = Baralhos(nome=linha["deck_name"], etiqueta_id=etiqueta.id)
                    session.add(baralho)
                    session.flush()
                    baralhos[baralho.nome] = baralho
                    resultado.baralhos_criados += 1

                chave = (baralho.id, linha["subtheme"], linha["question"])
                if chave in existentes:
                    resultado.cartas_ignoradas += 1
                    continue

                session.add(
                    Cartas(
                        frente=linha["subtheme"],
                        verso=linha["question"],
                        ativa=linha["active"],
                        criado_por_usuario_id=criado_por_usuario_id,
                        baralho_id=baralho.id,
                    )
                )
                existentes.add(chave)
                resultado.cartas_criadas += 1

            session.commit()
        except Exception:
            session.rollback()
            raise

        return resultado

    def _ler_csv(self, caminho: Path) -> list[dict]:
        # utf-8-sig remove o BOM que o Excel costuma colocar
        with caminho.open(newline="", encoding="utf-8-sig") as arquivo:
            cabecalho = arquivo.readline()
            arquivo.seek(0)
            # o Excel em pt-BR exporta com ";", outros com "," ou tab
            delimitador = max(",;\t", key=cabecalho.count)

            leitor = csv.DictReader(arquivo, delimiter=delimitador)
            faltando = [c for c in COLUNAS_OBRIGATORIAS if c not in (leitor.fieldnames or [])]
            if faltando:
                raise ValueError(f"Colunas ausentes no CSV: {', '.join(faltando)}")

            linhas = []
            for numero, bruta in enumerate(leitor, start=2):  # linha 1 é o cabeçalho
                linha = {c: (bruta.get(c) or "").strip() for c in COLUNAS_OBRIGATORIAS}
                for coluna in ("collection_name", "deck_name", "subtheme", "question"):
                    if not linha[coluna]:
                        raise ValueError(f"Linha {numero}: coluna '{coluna}' está vazia.")
                linha["active"] = self._converter_bool(linha["active"], numero)
                linhas.append(linha)

        return linhas

    def _converter_bool(self, valor: str, numero_linha: int) -> bool:
        valor_normalizado = valor.lower()
        if valor_normalizado in VALORES_VERDADEIROS:
            return True
        if valor_normalizado in VALORES_FALSOS:
            return False
        raise ValueError(f"Linha {numero_linha}: valor inválido em 'active': '{valor}'.")
