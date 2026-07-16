import Link from "next/link";
import Container from "./Container";
import MobileMenu from "./MobileMenu";

export default function Navbar() {
  const links = [
    { label: "Contato", value: "/", id: 2 },
    { label: "Cupons", value: "/", id: 3 },
  ];
  return (
    <nav className=" bg-surface border-b border-border ">
      <Container>
        <div className="flex justify-between items-center py-4">
          <Link href="/">
            <span className="font-sora text-base sm:text-lg font-medium text-text-primary">
              Vendura
            </span>
          </Link>

          <div className="hidden sm:flex justify-between items-center gap-6">
            {links.map((link) => (
              <Link
                key={link.id}
                href={link.value}
                className=" nav-link text-sm text-text-secondary  hover:text-accent transition-colors"
              >
                {link.label}
              </Link>
            ))}
          </div>

          <div className="flex items-center gap-4">
            <Link
              href="/login"
              className="px-2 sm:px-4 py-1.5 sm:py-2 bg-accent hover:bg-accent-hover rounded-lg text-white text-sm sm:text-base transition-colors duration-200 active:scale-98 focus:outline-none focus-visible:ring-3 focus-visible:ring-accent-hover focus-visible:ring-offset-2"
            >
              Login
            </Link>

            <MobileMenu links={links} />
          </div>
        </div>
      </Container>
    </nav>
  );
}
