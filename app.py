from flask import Flask, render_template, request, redirect, url_for, flash
import os

# Class utama yang mewarisi semua fitur
class KadatuanApps(Flask):
    def __init__(self):
        super().__init__(__name__)
        self.config['UPLOAD_FOLDER'] = 'uploads'
        self.secret_key = 'supersecretkey'
        if not os.path.exists(self.config['UPLOAD_FOLDER']):
            os.makedirs(self.config['UPLOAD_FOLDER'])

        self.add_routes()
# Menggunakan cara Lazy Loading untuk mengakses lebih cepat
    def get_data_selection(self):
        if not hasattr(self, '_data_selection'):
            from modules.data_selection import DataSelection
            self._data_selection = DataSelection()
        return self._data_selection

    def get_preprocessing(self):
        if not hasattr(self, '_preprocessing'):
            from modules.preprocessing import Preprocessing
            self._preprocessing = Preprocessing()
        return self._preprocessing

    def get_transformation(self):
        if not hasattr(self, '_transformation'):
            from modules.transformation import Transformation
            self._transformation = Transformation()
        return self._transformation

    def get_data_mining(self):
        if not hasattr(self, '_data_mining'):
            from modules.data_mining import DataMining
            self._data_mining = DataMining()
        return self._data_mining

    def get_recommendation(self):
        if not hasattr(self, '_recommendation'):
            from modules.recommendation import Recommendation
            self._recommendation = Recommendation()
        return self._recommendation

    def add_routes(self):
        self.add_url_rule('/', view_func=self.index)
        self.add_url_rule('/data_selection', view_func=self.data_selection_route, methods=['GET', 'POST'])
        self.add_url_rule('/preprocessing', view_func=self.preprocessing_route, methods=['GET', 'POST'])
        self.add_url_rule('/transformation', view_func=self.transformation_route, methods=['GET', 'POST'])
        self.add_url_rule('/data_mining', view_func=self.data_mining_route, methods=['GET', 'POST'])
        self.add_url_rule('/recommendation', view_func=self.recommendation_route, methods=['GET', 'POST'])


    def index(self):
        return redirect(url_for('data_selection_route'))

    def data_selection_route(self):
        if request.method == 'POST':
            uploaded_files = 0  # Counter untuk file yang berhasil diunggah

            # Periksa dan unggah file
            for file_key in ['Data Transaksi', 'Data Kuesioner']:
                file = request.files.get(file_key)
                if file and file.filename:
                    self.get_data_selection().handle_upload(file_key, file)
                    uploaded_files += 1

            # Validasi apakah kedua file telah diunggah
            if uploaded_files < 2:
                flash('Harap unggah kedua file (x`Data Transaksi dan Data Kuesioner) sebelum melanjutkan!', 'error')
                return redirect(url_for('data_selection_route'))

            # Jika kedua file berhasil diunggah
            flash('Data berhasil diunggah!', 'success')
            return redirect(url_for('data_selection_route'))

        return render_template('data_selection.html', data_files=self.get_data_selection().data_files)

    def preprocessing_route(self):
        if not self.get_data_selection().data_files:
            return redirect(url_for('data_selection_route'))

        self.get_preprocessing().handle_missing_data(self.get_data_selection().data_files)
        self.get_preprocessing().rfm_results = self.get_preprocessing().perform_rfm_analysis(self.get_preprocessing().data_transformed)

        return render_template(
            'preprocessing.html',
            data_transformed=self.get_preprocessing().data_transformed,
            missing_records=self.get_preprocessing().missing_records,
            rfm_results=self.get_preprocessing().rfm_results
        )

    def transformation_route(self):
        if self.get_preprocessing().rfm_results is None or self.get_preprocessing().rfm_results.empty:
            return redirect(url_for('preprocessing_route'))

        rfm = self.get_transformation().normalize_rfm(self.get_preprocessing().rfm_results)

        return render_template('transformation.html', transformed_rfm=rfm)

    def data_mining_route(self):
        if self.get_transformation().transformed_data is None or self.get_transformation().transformed_data.empty:
            return redirect(url_for('transformation_route'))

        if request.method == 'POST':
            num_clusters = int(request.form.get('num_clusters', 3))
            clustering_results, dbi_score = self.get_data_mining().apply_clustering(self.get_transformation().transformed_data, num_clusters)
            return render_template(
                'data_mining.html',
                clustering_results=clustering_results,
                dbi_score=dbi_score
            )

        return render_template('data_mining.html', clustering_results=None, dbi_score=None)

    def recommendation_route(self):
        if self.get_data_mining().clustering_results is None:
            return redirect(url_for('data_mining_route'))

        questionnaire_data = self.get_data_selection().data_files.get('Data Kuesioner')
        recommendations, merged_data = self.get_recommendation().generate_recommendations(
            self.get_data_mining().clustering_results, questionnaire_data
        )

        # Filter and rename columns for the questionnaire data
        if merged_data is not None:
            
            merged_data = merged_data[['Id Pelanggan', 'Nama Pelanggan', 'Nama Produk', 'Jenis Kelamin', 'Usia', 'Profesi', 'Hobi','No Hp', 'Cluster', 'Segment']].copy()
            merged_data.dropna(inplace=True)
            merged_data.reset_index(drop=True, inplace=True)
            merged_data.index += 1
            merged_data['No'] = merged_data.index
            merged_data = merged_data[['No', 'Id Pelanggan','Nama Pelanggan', 'Nama Produk', 'Jenis Kelamin', 'Usia', 'Profesi', 'Hobi','No Hp', 'Cluster', 'Segment']]

        return render_template(
            'recommendation.html',
            recommendations=recommendations,
            merged_data=merged_data
        )

if __name__ == '__main__':
    apps_kadatuan = KadatuanApps()
    apps_kadatuan.run(debug=True)