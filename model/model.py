from database.regione_DAO import RegioneDAO
from database.tour_DAO import TourDAO
from database.attrazione_DAO import AttrazioneDAO

class Model:
    def __init__(self):
        self.tour_map = {} # Mappa ID tour -> oggetti Tour
        self.attrazioni_map = {} # Mappa ID attrazione -> oggetti Attrazione

        self._pacchetto_ottimo = []
        self._valore_ottimo: int = -1
        self._costo = 0



        # Caricamento
        self.load_tour()
        self.load_attrazioni()
        self.load_relazioni()

    @staticmethod
    def load_regioni():
        """ Restituisce tutte le regioni disponibili """
        return RegioneDAO.get_regioni()

    def load_tour(self):
        """ Carica tutti i tour in un dizionario [id, Tour]"""
        self.tour_map = TourDAO.get_tour()

    def load_attrazioni(self):
        """ Carica tutte le attrazioni in un dizionario [id, Attrazione]"""
        self.attrazioni_map = AttrazioneDAO.get_attrazioni()

    def load_relazioni(self):
        """
            Interroga il database per ottenere tutte le relazioni fra tour e attrazioni e salvarle nelle strutture dati
            Collega tour <-> attrazioni.
            --> Ogni Tour ha un set di Attrazione.
            --> Ogni Attrazione ha un set di Tour.
        """
        relazioni = TourDAO.get_tour_attrazioni()
        for coppia in relazioni:

            coppia_tour = coppia['id_tour']
            coppia_attrazioni = coppia['id_attrazione']

            tour = self.tour_map[coppia_tour] # recupero l'OGGETTO Tour corrispondente all'id
            attr = self.attrazioni_map[coppia_attrazioni]

            tour.attrazioni.add(attr)  # aggiungo l'oggetto Attrazione al set di attrazioni del tour
            attr.tour.add(tour)


    def genera_pacchetto(self, id_regione: str, max_giorni: int = None, max_budget: float = None):
        """
        Calcola il pacchetto turistico ottimale per una regione rispettando i vincoli di durata, budget e attrazioni uniche.
        :param id_regione: id della regione
        :param max_giorni: numero massimo di giorni (può essere None --> nessun limite)
        :param max_budget: costo massimo del pacchetto (può essere None --> nessun limite)

        :return: self._pacchetto_ottimo (una lista di oggetti Tour)
        :return: self._costo (il costo del pacchetto)
        :return: self._valore_ottimo (il valore culturale del pacchetto)
        """
        self._pacchetto_ottimo = []
        self._costo = 0
        self._valore_ottimo = 0
        attrazioni_usate = set()
        durata_totale = 0

        for tour in self.tour_map.values():

            if tour.id_regione != id_regione:
                continue
            if max_giorni is not None and (durata_totale+ tour.durata_giorni) > max_giorni:
                continue
            if max_budget is not None and (self._costo + tour.costo) > max_budget:
                continue
            nuove_attrazioni = {a for a in tour.attrazioni if a not in attrazioni_usate}
            if not nuove_attrazioni:
                continue
            self._pacchetto_ottimo.append(tour)
            self._costo += tour.costo
            durata_totale += tour.durata_giorni

            for attr in nuove_attrazioni:
                attrazioni_usate.add(attr)
                self._valore_ottimo += attr.valore_culturale

        return self._pacchetto_ottimo, self._costo, self._valore_ottimo

    def _ricorsione(self, start_index, tours, pacchetto_parziale,
                    durata_corrente, costo_corrente, valore_corrente,
                    attrazioni_usate, max_giorni, max_budget):
        """ Backtracking per massimizzare il valore culturale """

        # Aggiorna pacchetto ottimale
        if valore_corrente > self._valore_ottimo:
            self._valore_ottimo = valore_corrente
            self._pacchetto_ottimo = list(pacchetto_parziale)
            self._costo = costo_corrente

        # Caso terminale
        if start_index == len(tours):
            return

        tour = tours[start_index]

        # NON PRENDERE il tour
        self._ricorsione(
            start_index + 1,
            tours,
            pacchetto_parziale,
            durata_corrente,
            costo_corrente,
            valore_corrente,
            attrazioni_usate,
            max_giorni,
            max_budget
        )

        #  PRENDERE il tour se possibile
        if max_giorni is not None and (durata_corrente + tour.durata_giorni )> max_giorni:
            return
        if max_budget is not None and( costo_corrente + tour.costo) > max_budget:
            return

        nuove_attr = {a for a in tour.attrazioni if a not in attrazioni_usate}
        if not nuove_attr:
            return

        pacchetto_parziale.append(tour)
        nuove_attr_usate = attrazioni_usate.union(nuove_attr)
        nuovo_valore = valore_corrente + sum(a.valore_culturale for a in nuove_attr)

        self._ricorsione(
            start_index + 1,
            tours,
            pacchetto_parziale,
            durata_corrente + tour.durata_giorni,
            costo_corrente + tour.costo,
            nuovo_valore,
            nuove_attr_usate,
            max_giorni,
            max_budget
        )

        # Backtracking: rimuovo il tour aggiunto
        pacchetto_parziale.pop()
