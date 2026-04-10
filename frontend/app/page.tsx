import Sidebar from '../components/Sidebar';
import Navbar from '../components/Navbar';
import ConciergeForm from '../components/ConciergeForm';
import styles from './page.module.css';

export default function Home() {
  return (
    <div className={styles.container}>
      <Sidebar />
      <main className={styles.mainContent}>
        <Navbar />
        <div className={styles.contentArea}>
          <header className={styles.header}>
            <h1 className={styles.title}>
              Tell us your <span>cravings</span>.
            </h1>
            <p className={styles.subtitle}>
              Fine-tune your palette. Our AI Concierge will curate a bespoke dining map based on your mood, location, and aesthetic preferences.
            </p>
          </header>
          
          <ConciergeForm />
        </div>
      </main>
    </div>
  );
}
