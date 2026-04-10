import React from 'react';
import styles from './Navbar.module.css';
import { Bell, Settings, User } from 'lucide-react';

export default function Navbar() {
  return (
    <nav className={styles.navbar}>
      <div className={styles.logo}>
        The Culinary Editorial
      </div>
      
      <div className={styles.navItems}>
        <a href="#" className={styles.navItem}>Cuisines</a>
        <a href="#" className={styles.navItem}>Collections</a>
        <a href="#" className={styles.navItem}>AI Discoveries</a>
        <a href="#" className={styles.navItem}>My Journal</a>
      </div>
      
      <div className={styles.actions}>
        <a href="#" className={styles.navItemActive}>Preferences</a>
        <button className={styles.iconBtn}><Bell size={20} /></button>
        <button className={styles.iconBtn}><Settings size={20} /></button>
        <div className={styles.avatar}>
          <User size={20} />
        </div>
      </div>
    </nav>
  );
}
