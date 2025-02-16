import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
from typing import List, Tuple
from tabulate import tabulate

class EvolutionAnalyzer:
    def __init__(self, data_path: str):
        """Initialize with Pokemon dataset."""
        self.df = pd.read_csv(data_path)
        # Core stats for analysis
        self.stat_columns = ['hp', 'attack', 'defense', 'sp_attack', 'sp_defense', 'speed']
        
    def get_evolution_chain(self, pokemon_name: str) -> List[str]:
        """Find evolution chain based on Pokedex numbers."""
        pokemon_row = self.df[self.df['name'] == pokemon_name].iloc[0]
        pokedex_num = pokemon_row['pokedex_number']
        
        # Look for potential evolutions (next 1-2 sequential numbers)
        evolution_chain = [pokemon_name]
        for i in range(1, 3):  # Check next 2 numbers
            next_form = self.df[self.df['pokedex_number'] == pokedex_num + i]
            if not next_form.empty:
                evolution_chain.append(next_form.iloc[0]['name'])
        
        return evolution_chain
    
    def calculate_evolution_value(self, base_pokemon: str) -> Tuple[dict, pd.DataFrame, list]:
        """Calculate the value of evolving a given Pokemon and provide recommendations."""
        evolution_chain = self.get_evolution_chain(base_pokemon)
        if len(evolution_chain) == 1:
            return {"message": f"{base_pokemon} has no evolutions."}, pd.DataFrame(), []
        
        # Get stats for each form
        evolution_stats = []
        for pokemon in evolution_chain:
            stats = self.df[self.df['name'] == pokemon][self.stat_columns].iloc[0]
            evolution_stats.append(stats)
        
        stats_df = pd.DataFrame(evolution_stats, index=evolution_chain)
        
        # Calculate stat changes and percentages
        changes = {}
        recommendations = []
        
        for i in range(1, len(evolution_chain)):
            prev_form = evolution_chain[i-1]
            current_form = evolution_chain[i]
            
            # Calculate individual stat changes and percentages
            stat_changes = stats_df.loc[current_form] - stats_df.loc[prev_form]
            stat_percentages = (stats_df.loc[current_form] / stats_df.loc[prev_form] - 1) * 100
            
            # Total stats
            total_change = sum(stat_changes)
            total_percent = (sum(stats_df.loc[current_form]) / sum(stats_df.loc[prev_form]) - 1) * 100
            
            changes[f"{prev_form} → {current_form}"] = {
                "total_stat_change": total_change,
                "percent_improvement": round(total_percent, 1),
                "biggest_boost": self._get_biggest_stat_change(stats_df.loc[prev_form], stats_df.loc[current_form]),
                "stat_changes": stat_changes,
                "stat_percentages": stat_percentages
            }
            
            # Generate recommendations
            for stat in self.stat_columns:
                if stat_percentages[stat] < -10:  # If stat decreases by more than 10%
                    recommendations.append(
                        f"⚠️ Don't evolve {prev_form} to {current_form} if you need {stat.replace('_', ' ')}: "
                        f"It decreases by {abs(round(stat_percentages[stat], 1))}%"
                    )
                elif stat_percentages[stat] > 30:  # If stat increases by more than 30%
                    recommendations.append(
                        f"✨ Consider evolving {prev_form} to {current_form} for {stat.replace('_', ' ')}: "
                        f"It increases by {round(stat_percentages[stat], 1)}%"
                    )
            
        return changes, stats_df, recommendations

    def _get_biggest_stat_change(self, prev_stats: pd.Series, new_stats: pd.Series) -> str:
        """Identify the stat with the biggest improvement."""
        changes = new_stats - prev_stats
        max_change = changes.max()
        stat = changes[changes == max_change].index[0]  # Fixed: use direct index access
        return f"{stat} (+{max_change})"

    def visualize_evolution_stats(self, stats_df: pd.DataFrame, save_path: str = 'evolution_stats.png') -> None:
        """Create a radar chart comparing stats across evolution forms.
        
        Args:
            stats_df: DataFrame containing Pokemon stats
            save_path: Path where to save the plot image (default: 'evolution_stats.png')
        """
        stats = stats_df.values
        angles = np.linspace(0, 2*np.pi, len(self.stat_columns), endpoint=False)
        
        # Close the plot by appending first value
        stats = np.concatenate((stats, stats[:, [0]]), axis=1)
        angles = np.concatenate((angles, [angles[0]]))
        
        fig, ax = plt.subplots(figsize=(10, 10), subplot_kw=dict(projection='polar'))
        
        for i, pokemon in enumerate(stats_df.index):
            ax.plot(angles, stats[i], 'o-', linewidth=2, label=pokemon)
            ax.fill(angles, stats[i], alpha=0.25)
        
        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(self.stat_columns)
        ax.legend(loc='upper right', bbox_to_anchor=(0.1, 0.1))
        plt.title("Evolution Stats Comparison")
        plt.savefig(save_path)  # Save the plot to a file
        plt.close()  # Close the figure to free memory

    def get_stat_change_table(self, changes: dict) -> str:
        """Create a formatted table of stat changes and recommendations."""
        table_data = []
        headers = ["Stat", "Change", "Impact", "Recommendation"]
        
        for evolution, stats in changes.items():
            table_data.append(["", "", "", ""])  # Empty row as separator
            table_data.append([f"⚡ {evolution}", "", "", ""])
            
            for stat in self.stat_columns:
                change = stats['stat_changes'][stat]
                percent = stats['stat_percentages'][stat]
                
                # Determine impact and recommendation
                if percent < -10:
                    impact = "🔻 Major Decrease"
                    recommendation = "❌ Keep unevolved"
                elif percent > 30:
                    impact = "⬆️ Major Boost"
                    recommendation = "✅ Evolve"
                elif percent > 0:
                    impact = "↗️ Minor Boost"
                    recommendation = "👍 Neutral/Positive"
                else:
                    impact = "↘️ Minor Decrease"
                    recommendation = "⚠️ Consider keeping"
                
                table_data.append([
                    stat.replace('_', ' ').title(),
                    f"{change:+.0f} ({percent:+.1f}%)",
                    impact,
                    recommendation
                ])
        
        return tabulate(table_data, headers=headers, tablefmt="grid")

def get_pokemon_with_fzf(pokemon_list: List[str]) -> str:
    """Use fzf to select a Pokemon from the list."""
    import subprocess
    import tempfile
    
    # Create a temporary file with Pokemon names
    with tempfile.NamedTemporaryFile(mode='w+') as tmp:
        tmp.write('\n'.join(pokemon_list))
        tmp.flush()
        
        # Run fzf and capture output
        try:
            result = subprocess.run(['fzf'], 
                                  input=open(tmp.name).read(),
                                  text=True,
                                  capture_output=True)
            if result.returncode == 0:
                return result.stdout.strip()
        except FileNotFoundError:
            print("❌ Error: fzf is not installed. Please install it first.")
            exit(1)
    return None

def main():
    analyzer = EvolutionAnalyzer('pokemon.csv')
    
    # Get list of available Pokemon
    available_pokemon = sorted(analyzer.df['name'].unique())
    
    while True:
        try:
            # Get Pokemon selection using fzf
            pokemon_name = get_pokemon_with_fzf(available_pokemon)
            
            if not pokemon_name:
                break  # User cancelled selection
            
            # Perform analysis
            changes, stats_df, _ = analyzer.calculate_evolution_value(pokemon_name)
            
            if "message" in changes:
                print(f"\n⚠️ {changes['message']}")
                continue
            
            print(f"\n🔍 Evolution Analysis for {pokemon_name}:")
            print("=" * 50)
            print(analyzer.get_stat_change_table(changes))
            
            # Visualize the evolution chain
            if not stats_df.empty:
                output_file = f"{pokemon_name.lower()}_evolution_stats.png"
                analyzer.visualize_evolution_stats(stats_df, save_path=output_file)
                print(f"\n📊 Evolution stats visualization saved to: {output_file}")
            
            input("\nPress Enter to search for another Pokemon (Ctrl+C to quit)...")
            
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ An error occurred: {e}")
            continue

if __name__ == "__main__":
    main()