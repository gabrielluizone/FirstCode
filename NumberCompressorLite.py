df = [int(n) for n in input('>> ').split(' ')]
df.sort()
uni = list(set(df))
uni.sort()
dic = dict(zip( uni , [df.count(n) for n in uni] ))
out = []
for i in dic:
  if dic[i] == 1:
    out.append(i)
  elif dic[i] == 2:
    out.extend([i, i])
  elif dic[i] == 3:
    out.extend([i, i, i])
  else:
    out.extend(['AA', i, dic[i]])
print(f'>> {out}')
