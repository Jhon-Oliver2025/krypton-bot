from technical_analysis import TechnicalAnalysis

def main():
    print("Iniciando sistema de monitoramento...")
    analyzer = TechnicalAnalysis()
    analyzer.start_monitoring()

if __name__ == "__main__":
    main()