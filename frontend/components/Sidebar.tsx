import React from 'react';
import styles from './Sidebar.module.css';
import { Home, Sparkles, TrendingUp, Bookmark, Award, User } from 'lucide-react';

export default function Sidebar() {
  return (
    <aside className={styles.sidebar}>
      <div className={styles.profileSection}>
        <div className={styles.avatarHex}>
          <User size={20} />
        </div>
        <div className={styles.profileInfo}>
          <h3>The Curator</h3>
          <p>ELITE TASTER STATUS</p>
        </div>
      </div>
      
      <ul className={styles.navLinks}>
        <li>
          <a href="#" className={styles.navLink}>
            <Home size={18} /> Home
          </a>
        </li>
        <li>
          <a href="#" className={`${styles.navLink} ${styles.navLinkActive}`}>
            <Sparkles size={18} /> AI Concierge
          </a>
        </li>
        <li>
          <a href="#" className={styles.navLink}>
            <TrendingUp size={18} /> Trending Now
          </a>
        </li>
        <li>
          <a href="#" className={styles.navLink}>
            <Bookmark size={18} /> Saved Tables
          </a>
        </li>
        <li>
          <a href="#" className={styles.navLink}>
            <Award size={18} /> Member Perks
          </a>
        </li>
      </ul>

      <button className={styles.bottomAction}>
        <Sparkles size={16} /> Ask AI Recommendation
      </button>
    </aside>
  );
}
