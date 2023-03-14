main = do putStrLn "Onverharo"
---------------------------------------------------------------------
-- Realizado com a ajuda do ChatGPT
-- Gabriel Luiz - 3º Ciclo de Ciência de Dados
-- Cálculo
---------------------------------------------------------------------
-- Desafio: Implementar a Derivada no Ponto
-- pt :: Double -> Func -> Double
-- 2.0 pontos para P1, com apresentação
---------------------------------------------------------------------
---------- Demonstrações
-- Função: f(x) = e^(x^2)
-- Derivada: ddx (Exp (Power X 2))
-- DerivVizual: render (ddx (Exp (Power X 2)))
-- DerivSimples: render (simplify (ddx (Exp (Power X 2))))
-- DerivPonto: pt 2 (Power X 2)
---------------------------------------------------------------------

-- Arvore de decisão da função
data Func = X -- f(x) = x
          | Sin Func -- f(x) = sen(g(x))
          | Cos Func -- f(x) = cos(g(x))
          | Exp Func -- f(x) = e^g(x)
          | Ln Func  -- f(x) = ln(g(x))
          | Power Func Double -- f(x) = g(x)^n
          | Const Double -- f(x) = k
          | Sum Func Func -- h(x)= f(x) + g(x)
          | Mult Func Func -- h(x) = f(x) * g(x)
          | Div  Func Func -- h(x) = (f(x) / g(x))
          deriving Show

-- A implantação da derivada no ponto pode ser feita utilizando o conceito de limite. Para isso, devemos ter a nossa função derivada e realizar o cálculo por meio de uma entrada. Como já podemos adquirir a derivada temos que calcular
ddx :: Func -> Func
ddx X = Const 1
ddx (Sin f) = Mult (Cos f) (ddx f)
ddx (Cos f) = Mult (Mult (Const (-1)) (Sin f)) (ddx f)
ddx (Exp f) = Mult (Exp f) (ddx f)
ddx (Ln f) = Mult (Div (Const 1) f) (ddx f)
ddx (Power f n) = Mult(Mult (Const n) (Power f (n-1))) (ddx f)
ddx (Sum f g) = Sum (ddx f) (ddx g)
ddx (Mult (Const k) f) = Mult (Const k) (ddx f)
ddx (Mult f g) = Sum (Mult (ddx f) g) (Mult f (ddx g))
ddx (Div f g) = Div (Sum (Mult (ddx f) g) (Mult (Const (-1)) (Mult f (ddx g)))) (Power g 2)
ddx (Const k) = Const 0

-- Porém é necessário um meio em que a derivada bruta seja interpretável para calcular a derivada num ponto. Por isso iremos convertê-lo para que o interpretador possa entender e calcular
eval :: Func -> Double -> Double
eval X x = x

eval (Sin f) x = sin (eval f x)
eval (Cos f) x = cos (eval f x)
eval (Exp f) x = exp (eval f x)
eval (Ln f) x = log (eval f x)
eval (Power f n) x = (eval f x) ** n
eval (Const k) x = k
eval (Sum f g) x = (eval f x) + (eval g x)
eval (Mult f g) x = (eval f x) * (eval g x)
eval (Div f g) x = (eval f x) / (eval g x)

-- Implementação da Derivada no Ponto:
-- Exemplos para ser testados no final do arquivo
pt :: Double -> Func -> Double
pt x f = eval (ddx f) x -- ddx (Sum (Power X 5) (Mult (Const 3) (Power X 4)))

-- [Bônus] Ao longo do processo desenvolvi (com ajuda do ChatGPT) um algoritmo que transforma a visualização da saída da derivável em uma mais fácil de visualização e se necessário, a eliminação de números irrelevantes na operação, como 1*1, use o simplify dentro de render se necessário e por questão de estética
render :: Func -> String
render X = "x"
render (Sin f) = "sin(" ++ render f ++ ")"
render (Cos f) = "cos(" ++ render f ++ ")"
render (Exp f) = "e^(" ++ render f ++ ")"
render (Ln f) = "ln(" ++ render f ++ ")"
render (Power f n) = "(" ++ render f ++ ")^" ++ show n
render (Const k) = show k
render (Sum f g) = render f ++ " + " ++ render g
render (Mult (Const k) f) = show k ++ render f
render (Mult f g) = render f ++ " " ++ render g
render (Div f g) = "(" ++ render f ++ ")/(" ++ render g ++ ")"

simplify :: Func -> Func
simplify (Mult (Const k1) (Const k2)) = Const (k1 * k2)
simplify (Mult (Const 1.0) f) = f
simplify (Mult f (Const 1.0)) = f
simplify (Mult (Const (-1.0)) (X)) = X
simplify (Mult (Const (-1.0)) f) = Mult (Const (-1.0)) (simplify f)
simplify (Mult f (Const (-1.0))) = Mult (Const (-1.0)) (simplify f)
simplify (Mult f g) = Mult (simplify f) (simplify g)
simplify (Sum (Const k1) (Const k2)) = Const (k1 + k2)
simplify (Sum f (Const 0.0)) = simplify f
simplify (Sum (Const 0.0) f) = simplify f
simplify (Sum f g) = Sum (simplify f) (simplify g)
simplify (Div f g) = Div (simplify f) (simplify g)
simplify f = f

---------------------------------------------------------------------

-- ddx (Sum (Power X 5) (Mult (Const 3) (Power X 4)))
-- x^5 + 3x^4 [--] 5x^4 + 12x^3
-- 1 = 17 | 2 = 176 | 3 = 729 | 9 = 41553

-- pt 9 (Sum (Power X 5) (Mult (Const 3) (Power X 4)))
-- pt 2 (Sum (Power X 5) (Mult (Const 3) (Power X 4)))

---------------------------------------------------------------------

-- ddx (Exp (Power X 2))
-- e^(x^2) [--] e^(x^2) * 2
-- 1 = 5.43656365 | 2 = 88,105.8631

-- pt 1 (Exp (Power X 2))
-- pt 2 (Exp (Power X 2))
---------------------------------------------------------------------

-- ddx (Mult (Exp (Mult (Const 2) (Power X 3))) (Cos (Mult (Const 3) X)))

-- pt 1 (Mult (Exp (Mult (Const 2) (Power X 3))) (Cos (Mult (Const 3) X)))
-- pt 2 (Mult (Exp (Mult (Const 2) (Power X 3))) (Cos (Mult (Const 3) X)))

---------------------------------------------------------------------