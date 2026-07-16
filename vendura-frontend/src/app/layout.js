import Navbar from "@/components/Navbar";
import { Inter, Sora } from "next/font/google";
import "./globals.css";
import Footer from "@/components/Footer";

const inter = Inter({ subsets: ["latin"], variable: "--font-inter" });
const sora = Sora({ subsets: ["latin"], variable: "--font-sora" });

export const metadata = {
  title: "Vendura",
  description: "Marketplace de produtos",
};

export default function RootLayout({ children }) {
  return (
    <html lang="pt-br">
      <body
        className={`${inter.variable} ${sora.variable} bg-background text-text-primary min-h-screen flex flex-col`}
      >
        <Navbar />
        {children}
        <Footer />
      </body>
    </html>
  );
}
