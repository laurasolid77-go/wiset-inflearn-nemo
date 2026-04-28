import pandas as pd
import sqlite3
import matplotlib.pyplot as plt
import koreanize_matplotlib
import os
import json
from sklearn.feature_extraction.text import TfidfVectorizer

# 1. 데이터 로드
def load_data():
    conn = sqlite3.connect('data/nemo_data.db')
    df = pd.read_sql_query("SELECT * FROM stores", conn)
    conn.close()
    
    # 숫자형 컬럼 변환 (SQLite에서는 TEXT로 저장되었을 수 있음)
    numeric_cols = ['deposit', 'monthlyRent', 'premium', 'sale', 'maintenanceFee', 'floor', 'groundFloor', 'size', 'viewCount', 'favoriteCount', 'areaPrice']
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
            
    return df

# 2. 기본 정보 출력 및 저장
def inspect_data(df):
    inspection = {}
    inspection['head'] = df.head().to_markdown()
    inspection['tail'] = df.tail().to_markdown()
    inspection['shape'] = df.shape
    inspection['duplicates'] = df.duplicated().sum()
    
    # info()는 stdout으로 출력되므로 별도 캡처 필요 없으나 보고서용으로 활용
    return inspection

# 3. 기술통계 및 시각화
def perform_eda(df):
    if not os.path.exists('images'):
        os.makedirs('images')
        
    # 수치형 기술통계
    num_desc = df.describe().to_markdown()
    
    # 범주형 기술통계
    cat_cols = df.select_dtypes(include=['object']).columns
    cat_desc_list = []
    for col in cat_cols:
        # 너무 많은 고유값을 가진 컬럼(ID 등) 제외
        if df[col].nunique() < 50:
            cat_desc_list.append(df[col].value_counts().head(30).to_frame().to_markdown())
    cat_desc = "\n\n".join(cat_desc_list)

    # 시각화 (10개 이상)
    plt.rcParams['figure.figsize'] = (12, 8)
    
    # 1. 보증금 분포 (Univariate)
    plt.figure()
    df['deposit'].hist(bins=30, color='skyblue', edgecolor='black')
    plt.title('보증금 분포')
    plt.xlabel('보증금')
    plt.ylabel('빈도')
    plt.savefig('images/01_deposit_dist.png')
    plt.close()

    # 2. 월세 분포 (Univariate)
    plt.figure()
    df['monthlyRent'].hist(bins=30, color='salmon', edgecolor='black')
    plt.title('월세 분포')
    plt.xlabel('월세')
    plt.ylabel('빈도')
    plt.savefig('images/02_rent_dist.png')
    plt.close()

    # 3. 보증금 vs 월세 (Bivariate)
    plt.figure()
    plt.scatter(df['deposit'], df['monthlyRent'], alpha=0.5, color='green')
    plt.title('보증금 vs 월세 상관관계')
    plt.xlabel('보증금')
    plt.ylabel('월세')
    plt.savefig('images/03_deposit_vs_rent.png')
    plt.close()

    # 4. 업종 중분류 빈도 (Categorical - Top 30)
    plt.figure()
    df['businessMiddleCodeName'].value_counts().head(30).plot(kind='bar', color='gold')
    plt.title('업종 중분류 빈도 (상위 30개)')
    plt.xticks(rotation=45)
    plt.savefig('images/04_business_middle_freq.png')
    plt.close()

    # 5. 층수별 평균 월세 (Bivariate)
    plt.figure()
    df.groupby('floor')['monthlyRent'].mean().sort_index().plot(kind='line', marker='o', color='purple')
    plt.title('층수별 평균 월세 변화')
    plt.xlabel('층수')
    plt.ylabel('평균 월세')
    plt.savefig('images/05_floor_vs_rent.png')
    plt.close()

    # 6. 전용면적 vs 월세 (Bivariate)
    plt.figure()
    plt.scatter(df['size'], df['monthlyRent'], alpha=0.5, color='orange')
    plt.title('전용면적 vs 월세')
    plt.xlabel('면적 (sqm)')
    plt.ylabel('월세')
    plt.savefig('images/06_size_vs_rent.png')
    plt.close()

    # 7. 지하철역 거리별 매물 수 (Categorical)
    if 'nearSubwayStation' in df.columns:
        plt.figure()
        df['nearSubwayStation'].value_counts().head(20).plot(kind='pie', autopct='%1.1f%%')
        plt.title('인근 지하철역 분포')
        plt.ylabel('')
        plt.savefig('images/07_subway_dist.png')
        plt.close()

    # 8. 면적 대비 가격(areaPrice) 분포 (Univariate)
    plt.figure()
    df['areaPrice'].plot(kind='box', color='red')
    plt.title('면적당 가격 분포')
    plt.savefig('images/08_area_price_box.png')
    plt.close()

    # 9. 월세 vs 관리비 (Bivariate)
    plt.figure()
    plt.scatter(df['monthlyRent'], df['maintenanceFee'], alpha=0.5, color='cyan')
    plt.title('월세 vs 관리비 상관관계')
    plt.xlabel('월세')
    plt.ylabel('관리비')
    plt.savefig('images/09_rent_vs_maint.png')
    plt.close()

    # 10. 가격 유형별 보증금 평균 (Multivariate context)
    plt.figure()
    df.groupby('priceTypeName')['deposit'].mean().plot(kind='barh', color='brown')
    plt.title('가격 유형별 평균 보증금')
    plt.savefig('images/10_price_type_avg_deposit.png')
    plt.close()

    # 4. TF-IDF 키워드 분석
    tfidf_table = ""
    if 'title' in df.columns:
        vectorizer = TfidfVectorizer(max_features=30)
        tfidf_matrix = vectorizer.fit_transform(df['title'].fillna(''))
        keywords = vectorizer.get_feature_names_out()
        sums = tfidf_matrix.sum(axis=0)
        data = []
        for col, capability in enumerate(keywords):
            data.append((capability, sums[0, col]))
        ranking = pd.DataFrame(data, columns=['keyword', 'tfidf_sum']).sort_values('tfidf_sum', ascending=False)
        
        tfidf_table = ranking.to_markdown()
        
        plt.figure()
        ranking.set_index('keyword')['tfidf_sum'].plot(kind='bar', color='teal')
        plt.title('매물 제목 키워드 TF-IDF 상위 30개')
        plt.xticks(rotation=45)
        plt.savefig('images/11_title_tfidf.png')
        plt.close()

    return num_desc, cat_desc, tfidf_table

class NumpyEncoder(json.JSONEncoder):
    def default(self, obj):
        import numpy as np
        if isinstance(obj, np.integer):
            return int(obj)
        if isinstance(obj, np.floating):
            return float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return super(NumpyEncoder, self).default(obj)

def main():
    df = load_data()
    inspect = inspect_data(df)
    num_desc, cat_desc, tfidf_table = perform_eda(df)
    
    # 결과를 임시 파일로 저장하여 보고서 작성 시 활용
    results = {
        "inspection": inspect,
        "num_desc": num_desc,
        "cat_desc": cat_desc,
        "tfidf_table": tfidf_table
    }
    with open('data/eda_results.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=4, cls=NumpyEncoder)
    
    print("EDA data generation completed.")

if __name__ == "__main__":
    main()
