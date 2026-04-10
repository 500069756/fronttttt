'use client';

import React, { useState, useEffect } from 'react';
import styles from './ConciergeForm.module.css';
import { MapPin, Target, Wallet, Star, X, Check, Sparkles, Loader2, Info } from 'lucide-react';

interface Restaurant {
  id: string;
  name: string;
  cuisines: string[];
  rating: number | null;
  cost_for_two: number | null;
  locality: string;
  explanation: string;
  rank: number;
}

interface RecommendResponse {
  items: Restaurant[];
  summary: string;
  meta: {
    prompt_version: string;
    relax_applied: boolean;
    degraded?: boolean;
    empty_reason?: string;
  };
}

export default function ConciergeForm() {
  const [budgetLabel, setBudgetLabel] = useState('$$');
  const [rating, setRating] = useState('4.5');
  const [cuisines, setCuisines] = useState(['Italian', 'Mexican', 'Thai']);
  const [location, setLocation] = useState('Banashankari'); // Broader area / City
  const [locality, setLocality] = useState('Banashankari'); // Neighborhood
  const [cities, setCities] = useState<string[]>([]);
  const [localities, setLocalities] = useState<string[]>([]);
  const [hierarchy, setHierarchy] = useState<Record<string, string[]>>({});
  const [isLoading, setIsLoading] = useState(false);
  const [isFetchingLocalData, setIsFetchingLocalData] = useState(false);
  const [results, setResults] = useState<RecommendResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const budgetMap: Record<string, number> = {
    '$': 500,
    '$$': 1000,
    '$$$': 2000,
    '$$$$': 5000
  };

  useEffect(() => {
    async function fetchLocationData() {
      setIsFetchingLocalData(true);
      try {
        const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8001';
        const res = await fetch(`${apiUrl}/api/v1/location-hierarchy`);
        if (res.ok) {
          const data = await res.json();
          setCities(data.cities || []);
          setHierarchy(data.hierarchy || {});
          
          if (data.cities && data.cities.length > 0) {
              const firstCity = data.cities[0];
              setCities(data.cities);
              // Only auto-select if current location is not in the list
              if (!data.cities.includes(location)) {
                  setLocation(firstCity);
              }
          }
        }
      } catch (err) {
        console.error('Failed to fetch location hierarchy', err);
      } finally {
        setIsFetchingLocalData(false);
      }
    }
    fetchLocationData();
  }, []);

  useEffect(() => {
    if (location && hierarchy[location]) {
        const availableLocalities = hierarchy[location];
        setLocalities(availableLocalities);
        // If current locality is not in the new city's localities, update it
        if (!availableLocalities.includes(locality)) {
            setLocality(availableLocalities[0] || '');
        }
    } else {
        setLocalities([]);
    }
  }, [location, hierarchy]);

  const toggleCuisine = (c: string) => {
    setCuisines(prev => prev.includes(c) ? prev.filter(x => x !== c) : [...prev, c]);
  };

  const handleGenerate = async () => {
    setIsLoading(true);
    setError(null);
    setResults(null);
    
    try {
      const payload = {
        city: location,
        location: locality,
        budget: budgetLabel === '$' ? 'low' : budgetLabel === '$$' ? 'medium' : 'high',
        cuisine: cuisines,
        min_rating: parseFloat(rating),
      };

      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8001';
      const res = await fetch(`${apiUrl}/api/v1/recommend`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload),
      });

      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        throw new Error(errData.detail || 'Failed to get recommendations');
      }

      const data = await res.json();
      setResults(data);
    } catch (err: any) {
      setError(err.message || 'Something went wrong');
    } finally {
      setIsLoading(false);
    }
  };

  const cuisinesList = [
    { name: 'Japanese', img: '/cuisine_japanese_sushi_1775681178337.png' },
    { name: 'Italian', img: '/cuisine_italian_pasta_1775681192970.png' },
    { name: 'Mexican', img: '/cuisine_mexican_tacos_1775681208830.png' },
    { name: 'French', img: '/cuisine_french_crepes_1775681259101.png' },
    { name: 'Indian', img: '/cuisine_italian_pasta_1775681192970.png' },
    { name: 'Thai', img: '/cuisine_japanese_sushi_1775681178337.png' },
  ];

  return (
    <div className={styles.formContainer}>
      <div className={styles.formGrid}>
        
        {/* Location Card */}
        <div className={`${styles.card} ${styles.locationCard}`}>
          <h2 className={styles.cardTitle}><MapPin className={styles.cardIcon} size={20} /> Current Location</h2>
          
          <div className={styles.inputGroup}>
            <label className={styles.inputLabel}>City</label>
            <div className={styles.inputWrapper}>
              <select 
                className={styles.locationInput} 
                value={location}
                onChange={(e) => setLocation(e.target.value)}
                disabled={isFetchingLocalData}
              >
                <option value="">Select an area...</option>
                {cities.map(l => (
                  <option key={l} value={l}>{l}</option>
                ))}
                {cities.length === 0 && <option value="Banashankari">Banashankari</option>}
              </select>
            </div>
          </div>

          <div className={styles.inputGroup}>
            <label className={styles.inputLabel}>Locality</label>
            <div className={styles.inputWrapper}>
              <select 
                className={styles.locationInput} 
                value={locality}
                onChange={(e) => setLocality(e.target.value)}
                disabled={isFetchingLocalData || !location}
              >
                <option value="">Select a sub-area...</option>
                {localities.map(l => (
                  <option key={l} value={l}>{l}</option>
                ))}
                {localities.length === 0 && <option value="Indiranagar">Indiranagar</option>}
              </select>
              <button className={styles.targetBtn}>
                {isFetchingLocalData ? <Loader2 className={styles.spin} size={18} /> : <Target size={18} />}
              </button>
            </div>
          </div>

          <div className={styles.mapVisual}>
            <img src="/minimalist_map_placeholder_1775681111265.png" alt="Map Illustration" className={styles.mapImg} />
          </div>
        </div>

        {/* Budget Card */}
        <div className={`${styles.card} ${styles.budgetCard}`}>
          <h2 className={styles.cardTitle}><Wallet className={styles.cardIcon} size={20} /> Budget Range</h2>
          <div className={styles.budgetOptions}>
            {Object.keys(budgetMap).map(item => (
              <button 
                key={item} 
                className={`${styles.budgetBtn} ${budgetLabel === item ? styles.active : ''}`}
                onClick={() => setBudgetLabel(item)}
              >
                {item}
              </button>
            ))}
          </div>
          <p className={styles.budgetHelper}>Up to ₹{budgetMap[budgetLabel]}</p>
        </div>

        {/* Rating Card */}
        <div className={`${styles.card} ${styles.ratingCard}`}>
          <h2 className={styles.cardTitle}><Star className={styles.cardIcon} size={20} /> Minimum Rating</h2>
          <div className={`${styles.radioOption} ${rating === '4.5' ? styles.active : ''}`} onClick={() => setRating('4.5')}>
            <span>4.5+ Exceptional</span>
            <div className={styles.radioCircle}></div>
          </div>
          <div className={`${styles.radioOption} ${rating === '4.0' ? styles.active : ''}`} onClick={() => setRating('4.0')}>
            <span>4.0+ Highly Rated</span>
            <div className={styles.radioCircle}></div>
          </div>
          <div className={`${styles.radioOption} ${rating === '3.5' ? styles.active : ''}`} onClick={() => setRating('3.5')}>
            <span>3.5+ Good</span>
            <div className={styles.radioCircle}></div>
          </div>
        </div>

        {/* Cuisines Card */}
        <div className={`${styles.card} ${styles.cuisinesCard}`}>
          <h2 className={styles.cardTitle}><X className={styles.cardIcon} size={20} /> Cuisine Cravings</h2>
          <div className={styles.cuisinesGrid}>
            {cuisinesList.map(c => {
              const active = cuisines.includes(c.name);
              return (
                <div 
                  key={c.name} 
                  className={`${styles.cuisineItem} ${active ? styles.active : ''}`}
                  style={{ backgroundImage: `url(${c.img})`, backgroundSize: 'cover', backgroundPosition: 'center' }}
                  onClick={() => toggleCuisine(c.name)}
                >
                  <div className={styles.cuisineCheck}>
                    <Check size={14} strokeWidth={3} />
                  </div>
                  <span className={styles.cuisineName}>{c.name}</span>
                </div>
              );
            })}
          </div>
        </div>

      </div>

      <div className={styles.submitContainer}>
        <button 
          className={`${styles.submitBtn} ${isLoading ? styles.loading : ''}`} 
          onClick={handleGenerate}
          disabled={isLoading || !locality || cuisines.length === 0}
        >
          {isLoading ? <Loader2 className={styles.spin} size={20} /> : <Sparkles size={20} />}
          {isLoading ? 'Curating your map...' : 'Generate Recommendations'}
        </button>
      </div>

      {error && (
        <div className={styles.errorContainer}>
          <Info size={18} />
          <span>{error}</span>
        </div>
      )}

      {results && (
        <div className={styles.resultsContainer}>
          <div className={styles.resultsHeader}>
            <h3 className={styles.resultsTitle}>Our Recommendations</h3>
            <p className={styles.resultsSummary}>{results.summary}</p>
          </div>
          
          <div className={styles.resultsGrid}>
            {results.items.length > 0 ? (
              results.items.map((item) => (
                <div key={item.id} className={styles.resultCard}>
                  <div className={styles.resultBadge}>#{item.rank}</div>
                  <div className={styles.resultInfo}>
                    <h4 className={styles.resultName}>{item.name}</h4>
                    <p className={styles.resultDetails}>
                      <Star size={14} className={styles.starIcon} /> {item.rating || 'N/A'} • {item.cuisines.join(', ')}
                    </p>
                    <p className={styles.resultLocality}>{item.locality} • ₹{item.cost_for_two} for two</p>
                    <div className={styles.explanation}>
                      <Sparkles size={12} className={styles.sparkleIcon} />
                      <p>{item.explanation}</p>
                    </div>
                  </div>
                </div>
              ))
            ) : (
              <p className={styles.noResults}>No restaurants found matching your criteria.</p>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
