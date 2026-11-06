import argparse

from sqlmodel import Session

from app.database import engine
from app.service.carta_service import CartaService


def main():
    parser = argparse.ArgumentParser(description="Importa cartas de um CSV para o banco.")
    parser.add_argument("csv", help="Caminho do arquivo CSV")
    parser.add_argument(
        "--usuario-id",
        type=int,
        required=True,
        help="ID do usuário que será registrado como criador das cartas",
    )
    args = parser.parse_args()

    with Session(engine) as session:
        resultado = CartaService().importar_csv(session, args.csv, args.usuario_id)

    print(
        f"Etiquetas criadas: {resultado.etiquetas_criadas} | "
        f"Baralhos criados: {resultado.baralhos_criados} | "
        f"Cartas criadas: {resultado.cartas_criadas} | "
        f"Cartas ignoradas (já existiam): {resultado.cartas_ignoradas}"
    )


if __name__ == "__main__":
    main()
