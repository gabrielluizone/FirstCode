# Compactador Numérico | Estrutura de Dados
df = [int(n) for n in input('Data Compression\n>> ').split(' ')]
df.sort()
uni = list(set(df))
uni.sort()
dic = dict(zip( uni , [df.count(n) for n in uni] ))
out = []
for i in dic:
  if dic[i] == 1:
    out.append(i)
    continue
  elif dic[i] == 2:
    out.extend([i, i])
    continue
  elif dic[i] == 3:
    out.extend([i, i, i])
    continue
  else:
    out.extend(['AA', i, dic[i]])
# prt serve para torna a visualização facil, sem aspas e colchetes
# coloque # no 'prt' e troque por 'out' para não usar poder computacional
prt = str(out)[1:-1].replace(',', '')
print(f'\nFull Compression\n>> {prt}')
