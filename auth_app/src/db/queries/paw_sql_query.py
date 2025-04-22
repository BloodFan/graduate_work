class UserQuery:
    @staticmethod
    def user_list(
        sort_column="u.created_at", sort_order="ASC", limit=10, offset=0
    ) -> str:
        return f"""
            SELECT
                u.id,
                u.login,
                u.email,
                u.first_name,
                u.last_name,
                u.is_active,
                array_agg(DISTINCT r.name) AS roles
            FROM
                users u
            LEFT JOIN
                userroles ur ON ur.user_id = u.id
            LEFT JOIN
                roles r ON r.id = ur.role_id
            GROUP BY
                u.id
            ORDER BY
                {sort_column} {sort_order}
            LIMIT :limit OFFSET :offset;
        """
