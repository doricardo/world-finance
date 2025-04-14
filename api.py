import requests

# URL base da API
BASE_URL = "https://jsonplaceholder.typicode.com/posts"


# Função para realizar uma chamada GET (obter todos os posts)
def get_posts():
    try:
        response = requests.get(BASE_URL)
        response.raise_for_status()  # Levanta uma exceção para códigos de erro HTTP
        print("GET Status Code:", response.status_code)
        print("GET Response (primeiros 2 posts):", response.json()[:2])  # Mostra apenas os 2 primeiros para brevidade
    except requests.exceptions.RequestException as e:
        print("Erro na chamada GET:", e)


# Função para realizar uma chamada GET por ID (obter um post específico)
def get_post_by_id(post_id):
    try:
        response = requests.get(f"{BASE_URL}/{post_id}")
        response.raise_for_status()
        print("GET by ID Status Code:", response.status_code)
        print("GET by ID Response:", response.json())
    except requests.exceptions.RequestException as e:
        print(f"Erro na chamada GET para ID {post_id}:", e)


# Função para realizar uma chamada POST (criar um post)
def create_post():
    payload = {
        "title": "Meu novo post",
        "body": "Este é o conteúdo do meu post de teste",
        "userId": 1
    }
    try:
        response = requests.post(BASE_URL, json=payload)
        response.raise_for_status()
        print("POST Status Code:", response.status_code)
        print("POST Response:", response.json())
    except requests.exceptions.RequestException as e:
        print("Erro na chamada POST:", e)


# Função para realizar uma chamada PUT (atualizar um post)
def update_post(post_id):
    payload = {
        "id": post_id,
        "title": "Post atualizado",
        "body": "Este é o conteúdo atualizado do post",
        "userId": 1
    }
    try:
        response = requests.put(f"{BASE_URL}/{post_id}", json=payload)
        response.raise_for_status()
        print("PUT Status Code:", response.status_code)
        print("PUT Response:", response.json())
    except requests.exceptions.RequestException as e:
        print(f"Erro na chamada PUT para ID {post_id}:", e)


# Função para realizar uma chamada DELETE (deletar um post)
def delete_post(post_id):
    try:
        response = requests.delete(f"{BASE_URL}/{post_id}")
        response.raise_for_status()
        print("DELETE Status Code:", response.status_code)
        print("DELETE Response: Post deletado com sucesso (resposta vazia esperada)")
    except requests.exceptions.RequestException as e:
        print(f"Erro na chamada DELETE para ID {post_id}:", e)


# Executando as funções
if __name__ == "__main__":
    print("=== Testando GET (todos os posts) ===")
    get_posts()

    print("\n=== Testando GET por ID (post 1) ===")
    get_post_by_id(1)

    print("\n=== Testando POST (criar post) ===")
    create_post()

    print("\n=== Testando PUT (atualizar post 1) ===")
    update_post(1)

    print("\n=== Testando DELETE (deletar post 1) ===")
    delete_post(1)