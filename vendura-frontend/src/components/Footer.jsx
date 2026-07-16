import Container from "./Container";

export default function Footer() {
  return (
    <footer className="bg-surface border-t border-border">
      <Container>
        <div className="flex flex-col sm:flex-row justify-between items-center py-6">
          <h1 className="text-text-secondary text-sm font-small">
            © {new Date().getFullYear()} Vendura. Todos os direitos reservados.
          </h1>
        </div>
      </Container>
    </footer>
  );
}
