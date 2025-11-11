import { useState } from "react";
import { useAuth } from "@/contexts/AuthContext";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { AlertCircle, FileText } from "lucide-react";
import { z } from "zod";

const emailSchema = z.string().email("Email inválido");
const passwordSchema = z.string().min(6, "Senha deve ter no mínimo 6 caracteres");

const Auth = () => {
  const { signIn, signUp } = useAuth();
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");
  const [validationErrors, setValidationErrors] = useState<{ [key: string]: string }>({});

  // Login state
  const [loginEmail, setLoginEmail] = useState("");
  const [loginPassword, setLoginPassword] = useState("");

  // Signup state
  const [signupEmail, setSignupEmail] = useState("");
  const [signupPassword, setSignupPassword] = useState("");
  const [signupFullName, setSignupFullName] = useState("");

  const validateField = (field: string, value: string, schema: z.ZodType) => {
    try {
      schema.parse(value);
      setValidationErrors(prev => ({ ...prev, [field]: "" }));
      return true;
    } catch (err) {
      if (err instanceof z.ZodError) {
        setValidationErrors(prev => ({ ...prev, [field]: err.issues[0].message }));
      }
      return false;
    }
  };

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setValidationErrors({});

    const emailValid = validateField("loginEmail", loginEmail, emailSchema);
    const passwordValid = validateField("loginPassword", loginPassword, passwordSchema);

    if (!emailValid || !passwordValid) return;

    setIsLoading(true);
    const { error } = await signIn(loginEmail, loginPassword);
    
    if (error) {
      if (error.message.includes("Invalid login credentials")) {
        setError("Email ou senha incorretos");
      } else if (error.message.includes("Email not confirmed")) {
        setError("Por favor, confirme seu email antes de fazer login");
      } else {
        setError(error.message);
      }
    }
    
    setIsLoading(false);
  };

  const handleSignup = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setValidationErrors({});

    const emailValid = validateField("signupEmail", signupEmail, emailSchema);
    const passwordValid = validateField("signupPassword", signupPassword, passwordSchema);
    const nameValid = signupFullName.trim().length > 0;

    if (!nameValid) {
      setValidationErrors(prev => ({ ...prev, signupFullName: "Nome é obrigatório" }));
    }

    if (!emailValid || !passwordValid || !nameValid) return;

    setIsLoading(true);
    const { error } = await signUp(signupEmail, signupPassword, signupFullName);
    
    if (error) {
      if (error.message.includes("User already registered")) {
        setError("Este email já está cadastrado. Faça login ou use outro email.");
      } else {
        setError(error.message);
      }
    }
    
    setIsLoading(false);
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-gradient-to-br from-background via-background to-primary/5 p-4">
      <Card className="w-full max-w-md">
        <CardHeader className="text-center">
          <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-gradient-primary">
            <FileText className="h-6 w-6 text-primary-foreground" />
          </div>
          <CardTitle className="text-2xl">Strukturis OCR</CardTitle>
          <CardDescription>
            Sistema profissional de OCR e processamento de documentos
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Tabs defaultValue="login" className="w-full">
            <TabsList className="grid w-full grid-cols-2">
              <TabsTrigger value="login">Login</TabsTrigger>
              <TabsTrigger value="signup">Cadastro</TabsTrigger>
            </TabsList>

            <TabsContent value="login">
              <form onSubmit={handleLogin} className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="login-email">Email</Label>
                  <Input
                    id="login-email"
                    type="email"
                    placeholder="seu@email.com"
                    value={loginEmail}
                    onChange={(e) => setLoginEmail(e.target.value)}
                    disabled={isLoading}
                    required
                  />
                  {validationErrors.loginEmail && (
                    <p className="text-sm text-destructive">{validationErrors.loginEmail}</p>
                  )}
                </div>

                <div className="space-y-2">
                  <Label htmlFor="login-password">Senha</Label>
                  <Input
                    id="login-password"
                    type="password"
                    placeholder="••••••••"
                    value={loginPassword}
                    onChange={(e) => setLoginPassword(e.target.value)}
                    disabled={isLoading}
                    required
                  />
                  {validationErrors.loginPassword && (
                    <p className="text-sm text-destructive">{validationErrors.loginPassword}</p>
                  )}
                </div>

                {error && (
                  <Alert variant="destructive">
                    <AlertCircle className="h-4 w-4" />
                    <AlertDescription>{error}</AlertDescription>
                  </Alert>
                )}

                <Button type="submit" className="w-full" disabled={isLoading}>
                  {isLoading ? "Entrando..." : "Entrar"}
                </Button>
              </form>
            </TabsContent>

            <TabsContent value="signup">
              <form onSubmit={handleSignup} className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="signup-name">Nome Completo</Label>
                  <Input
                    id="signup-name"
                    type="text"
                    placeholder="João Silva"
                    value={signupFullName}
                    onChange={(e) => setSignupFullName(e.target.value)}
                    disabled={isLoading}
                    required
                  />
                  {validationErrors.signupFullName && (
                    <p className="text-sm text-destructive">{validationErrors.signupFullName}</p>
                  )}
                </div>

                <div className="space-y-2">
                  <Label htmlFor="signup-email">Email</Label>
                  <Input
                    id="signup-email"
                    type="email"
                    placeholder="seu@email.com"
                    value={signupEmail}
                    onChange={(e) => setSignupEmail(e.target.value)}
                    disabled={isLoading}
                    required
                  />
                  {validationErrors.signupEmail && (
                    <p className="text-sm text-destructive">{validationErrors.signupEmail}</p>
                  )}
                </div>

                <div className="space-y-2">
                  <Label htmlFor="signup-password">Senha</Label>
                  <Input
                    id="signup-password"
                    type="password"
                    placeholder="••••••••"
                    value={signupPassword}
                    onChange={(e) => setSignupPassword(e.target.value)}
                    disabled={isLoading}
                    required
                  />
                  {validationErrors.signupPassword && (
                    <p className="text-sm text-destructive">{validationErrors.signupPassword}</p>
                  )}
                </div>

                {error && (
                  <Alert variant="destructive">
                    <AlertCircle className="h-4 w-4" />
                    <AlertDescription>{error}</AlertDescription>
                  </Alert>
                )}

                <Button type="submit" className="w-full" disabled={isLoading}>
                  {isLoading ? "Cadastrando..." : "Cadastrar"}
                </Button>
              </form>
            </TabsContent>
          </Tabs>
        </CardContent>
      </Card>
    </div>
  );
};

export default Auth;
