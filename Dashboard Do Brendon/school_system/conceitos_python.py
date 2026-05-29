"""
CONCEITOS DE CLASSES EM PYTHON
================================
Este arquivo explica os conceitos fundamentais de Programação Orientada a Objetos (POO)
usados no sistema de gestão de escola.
"""

# ============================================================================
# 1. CONCEITO BÁSICO: O QUE É UMA CLASSE?
# ============================================================================
"""
Uma classe é um "molde" ou "blueprint" para criar objetos.
Objetos são instâncias de classes que contêm dados (atributos) e comportamentos (métodos).
"""

class Pessoa:
    """
    Exemplo básico de uma classe.
    Atributos: características da pessoa (nome, idade)
    Métodos: ações que a pessoa pode fazer
    """
    
    def __init__(self, nome, idade):
        """
        __init__ é o construtor. Executado quando criamos uma nova instância.
        self representa a instância do objeto.
        """
        self.nome = nome
        self.idade = idade
    
    def apresentar(self):
        """Um método que retorna informações da pessoa"""
        return f"Olá, meu nome é {self.nome} e tenho {self.idade} anos"

# Criando objetos (instâncias) da classe Pessoa
pessoa1 = Pessoa("João", 30)
pessoa2 = Pessoa("Maria", 25)

print(pessoa1.apresentar())  # Olá, meu nome é João e tenho 30 anos
print(pessoa2.apresentar())  # Olá, meu nome é Maria e tenho 25 anos


# ============================================================================
# 2. HERANÇA: REUTILIZAR CÓDIGO DE OUTRAS CLASSES
# ============================================================================
"""
Herança permite que uma classe "herde" atributos e métodos de outra classe.
Evita duplicação de código.
"""

class Funcionario(Pessoa):
    """
    Funcionario herda de Pessoa.
    Possui todos os atributos e métodos de Pessoa, mais seus próprios.
    """
    
    def __init__(self, nome, idade, matricula, salario):
        super().__init__(nome, idade)  # Chama o construtor da classe pai
        self.matricula = matricula
        self.salario = salario
    
    def calcular_desconto_irrf(self):
        """Método exclusivo de Funcionario"""
        return self.salario * 0.15

# Usando herança
funcionario = Funcionario("Carlos", 40, "MAT001", 3000)
print(funcionario.apresentar())  # Herda o método de Pessoa
print(f"IRRF a pagar: R$ {funcionario.calcular_desconto_irrf()}")


# ============================================================================
# 3. ENCAPSULAMENTO: PROTEGER DADOS
# ============================================================================
"""
Encapsulamento controla o acesso aos atributos.
- Atributos públicos: acessíveis de qualquer lugar
- Atributos privados (_): por convenção, não acessar de fora
- Atributos privados (__): verdadeiramente privados (name mangling)
"""

class ContaBancaria:
    """Exemplo de encapsulamento"""
    
    def __init__(self, titular, saldo):
        self.titular = titular
        self.__saldo = saldo  # Atributo privado (__)
    
    def depositar(self, valor):
        """Método público para acessar o saldo privado"""
        if valor > 0:
            self.__saldo += valor
            return True
        return False
    
    def sacar(self, valor):
        """Só permite sacar se houver saldo"""
        if 0 < valor <= self.__saldo:
            self.__saldo -= valor
            return True
        return False
    
    def obter_saldo(self):
        """Acesso controlado ao saldo"""
        return self.__saldo

conta = ContaBancaria("João", 1000)
conta.depositar(500)
print(f"Saldo: R$ {conta.obter_saldo()}")  # R$ 1500
# conta.__saldo não pode ser acessado diretamente de fora


# ============================================================================
# 4. POLIMORFISMO: MESMA INTERFACE, COMPORTAMENTOS DIFERENTES
# ============================================================================
"""
Polimorfismo permite que objetos de diferentes classes respondam ao mesmo método
de formas diferentes.
"""

class Animal:
    def fazer_som(self):
        pass

class Cachorro(Animal):
    def fazer_som(self):
        return "Au au!"

class Gato(Animal):
    def fazer_som(self):
        return "Miau!"

class Passaro(Animal):
    def fazer_som(self):
        return "Piu piu!"

# Polimorfismo: mesma função, comportamentos diferentes
animais = [Cachorro(), Gato(), Passaro()]
for animal in animais:
    print(animal.fazer_som())  # Cada um faz seu som


# ============================================================================
# 5. ABSTRAÇÃO: ESCONDER COMPLEXIDADE
# ============================================================================
"""
Abstração define a interface sem mostrar os detalhes de implementação.
"""

from abc import ABC, abstractmethod

class Veiculo(ABC):
    """Classe abstrata define o que todo veículo deve ter"""
    
    @abstractmethod
    def acelerar(self):
        pass
    
    @abstractmethod
    def frear(self):
        pass

class Carro(Veiculo):
    def acelerar(self):
        return "Carro acelerou!"
    
    def frear(self):
        return "Carro freou!"

class Bicicleta(Veiculo):
    def acelerar(self):
        return "Bicicleta ganhou velocidade!"
    
    def frear(self):
        return "Bicicleta freou com o pedal!"

# Não podemos criar Veiculo diretamente (é abstrata)
# veiculo = Veiculo()  # ERRO!

# Mas podemos criar instâncias das subclasses
carro = Carro()
print(carro.acelerar())


# ============================================================================
# 6. APLICAÇÃO PRÁTICA: SISTEMA DE ESCOLA
# ============================================================================

class Usuario:
    """Classe base para todos os usuários do sistema"""
    
    def __init__(self, nome, email, cpf):
        self.nome = nome
        self.email = email
        self.cpf = cpf
    
    def obter_info(self):
        return f"Nome: {self.nome}, Email: {self.email}, CPF: {self.cpf}"


class Aluno(Usuario):
    """Aluno herda de Usuario"""
    
    def __init__(self, nome, email, cpf, matricula):
        super().__init__(nome, email, cpf)
        self.matricula = matricula
        self.notas = []
        self.frequencia = 0
    
    def adicionar_nota(self, disciplina, nota):
        self.notas.append({"disciplina": disciplina, "nota": nota})
    
    def calcular_media(self):
        if not self.notas:
            return 0
        return sum([n["nota"] for n in self.notas]) / len(self.notas)
    
    def obter_info(self):
        return f"{super().obter_info()}, Matrícula: {self.matricula}, Média: {self.calcular_media()}"


class Professor(Usuario):
    """Professor herda de Usuario"""
    
    def __init__(self, nome, email, cpf, matricula_prof, disciplinas):
        super().__init__(nome, email, cpf)
        self.matricula_prof = matricula_prof
        self.disciplinas = disciplinas
    
    def adicionar_disciplina(self, disciplina):
        self.disciplinas.append(disciplina)
    
    def obter_info(self):
        return f"{super().obter_info()}, Disciplinas: {', '.join(self.disciplinas)}"


class Turma:
    """Turma agrupa alunos e professor"""
    
    def __init__(self, codigo, nome, professor, semestre):
        self.codigo = codigo
        self.nome = nome
        self.professor = professor
        self.semestre = semestre
        self.alunos = []
    
    def adicionar_aluno(self, aluno):
        self.alunos.append(aluno)
    
    def listar_alunos(self):
        return [aluno.obter_info() for aluno in self.alunos]
    
    def calcular_media_turma(self):
        if not self.alunos:
            return 0
        medias = [aluno.calcular_media() for aluno in self.alunos]
        return sum(medias) / len(medias)


# Exemplo de uso
if __name__ == "__main__":
    print("\n" + "="*70)
    print("SISTEMA DE GESTÃO DE ESCOLA - CONCEITOS")
    print("="*70 + "\n")
    
    # Criando professor
    prof = Professor("Ana Silva", "ana@escola.com", "12345678900", "PROF001", ["Matemática"])
    print(prof.obter_info())
    
    # Criando alunos
    aluno1 = Aluno("João Santos", "joao@escola.com", "11111111111", "ALN001")
    aluno1.adicionar_nota("Matemática", 8.5)
    aluno1.adicionar_nota("Matemática", 9.0)
    
    aluno2 = Aluno("Maria Silva", "maria@escola.com", "22222222222", "ALN002")
    aluno2.adicionar_nota("Matemática", 7.0)
    aluno2.adicionar_nota("Matemática", 8.0)
    
    # Criando turma
    turma = Turma("TUR001", "Turma A - Matemática", prof, "2024.1")
    turma.adicionar_aluno(aluno1)
    turma.adicionar_aluno(aluno2)
    
    print(f"\n{'='*70}")
    print(f"TURMA: {turma.nome}")
    print(f"Professor: {turma.professor.nome}")
    print(f"{'='*70}")
    
    for info in turma.listar_alunos():
        print(info)
    
    print(f"\nMédia da turma: {turma.calcular_media_turma():.2f}")
