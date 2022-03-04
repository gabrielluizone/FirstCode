#Exercicio3
Nome = input("Digite o nome do Aluno ->\t")
Sobnome = input("Digite o Sobre Nome do Aluno ->\t")

print("\n\n========= >> Digite as Notas de Cada Matéria << =========")
Port = float(input("\nNota de Portugues:\t"))
Mat = float(input("Nota de Matemática:\t"))
Hist = float(input("Nota de História:\t"))
Geo = float(input("Nota de Geografia:\t"))
EdFisica = float(input("Nota de Ed. Física:\t"))

print("\n\n=========== >> Média << ===========")
print("\n\nNome do Aluno: ", Nome + "\t" + Sobnome)
media = (Port+Mat+Hist+Geo+EdFisica) / 5
print("A Média Final do Aluno: ", media)

#Exercicio - 4 (if)
print("\n\n========== >> Resultado << ==========")
if media >= 5.0:
    print("\n\nMédia Maior/Igual a 5: ", media >= 5.0)
    print(Nome + "\t" + Sobnome,"foi Aprovado")
if media < 5.0:
    print("Média inferior a 5: ", media < 5.0)
    print(Nome + "\t" + Sobnome,"foi Reprovado")

#exercicio - 5 (if e else)    
print("\n\n========== >> If e Else << ==========")
if media >= 5.0:
    print("\n\nMédia Maior/Igual a 5: ", media >= 5.0)
    print(Nome,"foi Aprovado 😀😀😀")
else:
    print("\n\nMédia Inferior a 5", media < 5.0)
    print(Nome,"Infelizmente foi Reprovado 😞😞😞")