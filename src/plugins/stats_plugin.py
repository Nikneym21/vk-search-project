from typing import List, Dict

class StatsPlugin:
    """Плагин для подсчёта итоговых метрик задачи: SI и просмотры."""
    @staticmethod
    def calculate_stats(posts: List[Dict]) -> Dict:
        total_likes = 0
        total_comments = 0
        total_reposts = 0
        total_views = 0
        for post in posts:
            likes = post.get('likes') or 0
            comments = post.get('comments') or 0
            reposts = post.get('reposts') or post.get('shares') or 0
            views = post.get('views') or 0
            try:
                likes = int(likes)
            except Exception:
                likes = 0
            try:
                comments = int(comments)
            except Exception:
                comments = 0
            try:
                reposts = int(reposts)
            except Exception:
                reposts = 0
            try:
                views = int(views)
            except Exception:
                views = 0
            total_likes += likes
            total_comments += comments
            total_reposts += reposts
            total_views += views
        return {
            'total_likes': total_likes,
            'total_comments': total_comments,
            'total_reposts': total_reposts,
            'total_SI': total_likes + total_comments + total_reposts,
            'total_views': total_views
        } 