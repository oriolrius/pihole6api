class PiHole6Metrics:
    def __init__(self, connection):
        """
        Handles Pi-hole metrics and stats API endpoints.
        :param connection: Instance of PiHole6Connection for API requests.
        """
        self.connection = connection

    # History API Endpoints
    def get_history(self):
        """Get activity graph data"""
        return self.connection.get("history")

    def get_history_clients(self):
        """Get per-client activity graph data"""
        return self.connection.get("history/clients")

    def get_history_database(self):
        """Get long-term activity graph data"""
        return self.connection.get("history/database")

    def get_history_database_clients(self):
        """Get per-client long-term activity graph data"""
        return self.connection.get("history/database/clients")

    # Query API Endpoints
    def get_queries(self):
        """Get query log"""
        return self.connection.get("queries")

    def get_query_suggestions(self):
        """Get query filter suggestions"""
        return self.connection.get("queries/suggestions")

    # Stats Database API Endpoints
    def get_stats_database_query_types(self):
        """Get query types (long-term database)"""
        return self.connection.get("stats/database/query_types")

    def get_stats_database_summary(self):
        """Get database content details"""
        return self.connection.get("stats/database/summary")

    def get_stats_database_top_clients(self):
        """Get top clients (long-term database)"""
        return self.connection.get("stats/database/top_clients")

    def get_stats_database_top_domains(self):
        """Get top domains (long-term database)"""
        return self.connection.get("stats/database/top_domains")

    def get_stats_database_upstreams(self):
        """Get upstream metrics (long-term database)"""
        return self.connection.get("stats/database/upstreams")

    # Stats API Endpoints
    def get_stats_query_types(self):
        """Get current query types"""
        return self.connection.get("stats/query_types")

    def get_stats_recent_blocked(self):
        """Get most recently blocked domain"""
        return self.connection.get("stats/recent_blocked")

    def get_stats_summary(self):
        """Get an overview of Pi-hole activity"""
        return self.connection.get("stats/summary")

    def get_stats_top_clients(self):
        """Get top clients"""
        return self.connection.get("stats/top_clients")

    def get_stats_top_domains(self):
        """Get top domains"""
        return self.connection.get("stats/top_domains")

    def get_stats_upstreams(self):
        """Get upstream destinations"""
        return self.connection.get("stats/upstreams")
