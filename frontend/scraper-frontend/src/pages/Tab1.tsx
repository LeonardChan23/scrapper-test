import React, { useState } from 'react';
import { IonContent, IonHeader, IonPage, IonTitle, IonToolbar, IonList, IonCard, IonCardHeader, IonCardTitle, IonCardContent, IonLabel, IonImg, IonGrid, IonRow, IonCol, IonSelect, IonSelectOption, IonButton, IonSpinner, IonItem } from '@ionic/react';
import { useQuery, gql } from '@apollo/client';
import './Tab1.css';

// 定义 GraphQL 查询
const GET_ITEMS = gql`
  query Query($sort: SortOrder, $filter: String) {
    items(sort: $sort, filter: $filter) {
      title
      author
      time
      link
      image
      source
      summary
    }
  }
`;

const formatDateTime = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString(); // 只保留日期
};

const Tab1: React.FC = () => {
    const [sort, setSort] = useState<string>('ASC'); // 默认排序为升序
    const [filter, setFilter] = useState<string>('All'); // 默认过滤为所有

    const { loading, error, data } = useQuery(GET_ITEMS, {
        variables: { sort, filter },
        skip: false,
    });

    const handleFilterChange = (event: CustomEvent) => {
        setFilter(event.detail.value);
    };

    const handleSortChange = (event: CustomEvent) => {
        setSort(event.detail.value);
    };

    if (loading) return <IonContent><IonSpinner /></IonContent>;
    if (error) return <IonContent>Error: {error.message}</IonContent>;

    const items = data?.items || [];

    return (
        <IonPage>
            <IonHeader>
                <IonToolbar>
                    <IonTitle>Scraper Blog</IonTitle>
                </IonToolbar>
            </IonHeader>
            <IonContent>
                <IonGrid style={{'max-width':'1600px'}}>
                    <IonRow>
                        <IonCol size="12" size-md="4">
                            <IonSelect placeholder="Select Sort Order" value={sort} onIonChange={handleSortChange} style={{ marginBottom: '16px' }}>
                                <IonSelectOption value="ASC">Ascending</IonSelectOption>
                                <IonSelectOption value="DESC">Descending</IonSelectOption>
                            </IonSelect>
                        </IonCol>
                        <IonCol size="12" size-md="4">
                            <IonSelect placeholder="Select Blog Source" value={filter} onIonChange={handleFilterChange} style={{ marginBottom: '16px' }}>
                                <IonSelectOption value='All'>All</IonSelectOption>
                                <IonSelectOption value="Ethereum">Ethereum</IonSelectOption>
                                <IonSelectOption value="protocol.ai">protocol.ai</IonSelectOption>
                                <IonSelectOption value="Coinbase">Coinbase</IonSelectOption>
                            </IonSelect>
                        </IonCol>
                        <IonCol size="12" size-md="4">
                            <IonButton expand="full" style={{ marginBottom: '16px' }}>
                                Fetch Data
                            </IonButton>
                        </IonCol>
                    </IonRow>

                    <IonRow>
                        {items.length > 0 ? (
                            items.map((item: { title: string; author: string; time: string; link: string; image: string; source: string; summary: string }) => (
                                <IonCol size="12" size-md="4" key={item.link} style={{ marginBottom: '16px' }}>
                                    <IonCard style={{ height: '400px' }}>
                                        <IonImg src={item.image} alt={item.title} className="card-image" />
                                        <IonCardHeader>
                                            <IonCardTitle>{item.title}</IonCardTitle>
                                        </IonCardHeader>
                                        <IonCardContent className="card-content">
                                            <IonLabel>
                                                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                                                    <span><strong>By {item.author} from {item.source}</strong></span>
                                                    <span><strong>{formatDateTime(item.time)}</strong></span>
                                                </div>
                                                <p className="summary">{item.summary}</p>
                                            </IonLabel>
                                        </IonCardContent>
                                    </IonCard>
                                </IonCol>
                            ))
                        ) : (
                            <IonItem>
                                <IonLabel>No items found.</IonLabel>
                            </IonItem>
                        )}
                    </IonRow>
                </IonGrid>
            </IonContent>
        </IonPage>
    );
};

export default Tab1;