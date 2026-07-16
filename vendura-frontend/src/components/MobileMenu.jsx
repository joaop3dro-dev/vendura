"use client";

import Link from "next/link";
import { useState } from "react";

export default function MobileMenu({ links }) {
  const [isOpen, setIsOpen] = useState(false);
  return (
    <div className="relative">
      <button
        className="block sm:hidden border-2 border-border px-3 py-1 rounded-lg text-text-primary cursor-pointer"
        onClick={() => setIsOpen(!isOpen)}
      >
        {isOpen ? "✖" : "⋮"}
      </button>

      {isOpen && (
        <div className="absolute top-full right-0 sm:hidden bg-gray-200 px-6 py-4 mt-2 rounded-lg flex flex-col gap-2">
          {links.map((link) => (
            <Link
              key={link.id}
              href={link.value}
              className=" nav-link text-base text-text-secondary  hover:text-accent transition-colors"
            >
              {link.label}
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
