import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'Hollowdeep — Mordor 3.0',
  description: 'A modern doorway into the original Mordor 3.0 multi-user dungeon. Enter the world, choose your character, and write your own adventure.',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return <html lang="en"><body>{children}</body></html>;
}
